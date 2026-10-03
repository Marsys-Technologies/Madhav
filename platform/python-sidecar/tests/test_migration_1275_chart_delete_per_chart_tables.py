"""
Migration 1275 (Suvarna, SS ruling N-108): PRIVACY GAP -- every per-chart row must leave when its chart is deleted.
chart_id -> charts(id) ON DELETE CASCADE on phala_muhurta, phala_mitigation, phala_phaladesa and every mimamsa_* table
with per-chart rows (27 tables). HELD: own draft PR, merges only after S-L1 and only on SS's review, TOGETHER WITH 1265.

Two tiers:
  * STATIC (always runs, DB-free): file shape, the ONE table list, guards, header sections.
  * LIVE (needs PostgreSQL server binaries): applies the REAL migration file, AS amjis_app, to a DISPOSABLE cluster this module
    creates with initdb in a temp dir (unix socket only, trust auth, removed at session end). It never connects to anything
    else. Skipped, loudly, when no initdb/pg_ctl is found; REQUIRE_PG_BINARIES=1 turns the skip into a failure. $PG_BIN pins a
    version; with PG_BINS (a path list) every listed major version is run (production is PostgreSQL 15.18).
    The cluster MIRRORS production's privilege layout (read 2026-10-03): schema public is owned by data_plane_schema_owner and
    amjis_app has USAGE only (NO CREATE), while amjis_app owns every table involved.

The fixture reproduces the 27 tables' chart_id shape (NOT NULL, leading index), mimamsa_predictions with its real 21 columns and
PK, the SET NULL links between the phala tables, charts, build_runs, chart_subject_consent and chart_subject_deletion_disputes
(both cascade from charts, as in production).

THE 1265 PART. 1265's frozen-row guard (PR #3033) is applied to mimamsa_predictions in three variants (the function body is the
exact text of 1265's head eb2432707, md5-pinned, in fixtures/):
  head       1265 as it stands: a DELETE is allowed only by the consent-withdrawal exception;
  notexists  head + the chart-deletion discriminator NOT EXISTS (SELECT 1 FROM public.charts WHERE id = OLD.chart_id);
  depth      head + the rejected discriminator pg_trigger_depth() > 1.
and proves on PostgreSQL: with `head` a chart delete FAILS (so 1265 must change); with `notexists` a chart delete removes ALL the
chart's rows in every covered table (predictions included) while a direct DELETE of a prediction -- by any role, owner and
superuser included -- stays refused, and a role that can create triggers cannot spoof it; with `depth` that spoof SUCCEEDS.

A mutation section rewrites the real SQL and requires every mutant to be caught. It does NOT prove production state.
"""
from __future__ import annotations

import glob
import hashlib
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_MIG = _REPO / "platform" / "migrations"
_M1275 = _MIG / "1275_chart_delete_reaches_phala_and_mimamsa_per_chart_tables.sql"
_GUARD_BODY = Path(__file__).resolve().parent / "fixtures" / "m1265_frozen_row_guard_body_head_eb2432707.plpgsql"
_REAL = _M1275.read_text()
GUARD_BODY_MD5 = "70dcc9d662869bad9c535968100ab0ed"

PHALA = ["phala_muhurta", "phala_mitigation", "phala_phaladesa"]
MIMAMSA = ["mimamsa_adjudication_log", "mimamsa_anchor_adjustment", "mimamsa_attribution", "mimamsa_calibration",
           "mimamsa_calibration_snapshot", "mimamsa_convergence_adjustment", "mimamsa_discoveries", "mimamsa_event_provenance",
           "mimamsa_export_log", "mimamsa_fact_adjustment", "mimamsa_insight_embeddings", "mimamsa_insight_units",
           "mimamsa_intervention_ledger", "mimamsa_journal", "mimamsa_load_bearing", "mimamsa_manifestation_grammar",
           "mimamsa_manifestation_sets", "mimamsa_multipliers", "mimamsa_predictions", "mimamsa_qa_eval", "mimamsa_reliability",
           "mimamsa_resonance_feedback", "mimamsa_signal_adjustment", "mimamsa_snapshot_cosign"]
TABLES = PHALA + MIMAMSA
RELINK = ["mimamsa_pool_contributions"]  # existing NO ACTION chart link -> CASCADE (SS N-108 addendum)
ALL_TABLES = TABLES + RELINK
OLD_POOL_DEF = "FOREIGN KEY (chart_id) REFERENCES charts(id)"
CONS = [f"{t}_chart_id_fkey" for t in TABLES]
POOL_CON = "mimamsa_pool_contributions_chart_id_fkey"
EXPECTED_DEF = "FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE"
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
ACTIVE_ASSETS = ["mi_bhavisya", "mi_abhilekha", "mi_kula", "ph_muhurta", "ph_pratikara", "ph_phaladesa"]


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


# -- STATIC tier --------------------------------------------------------------------

def test_guard_fixture_is_the_exact_1265_head_function_body():
    assert hashlib.md5(_GUARD_BODY.read_text().encode()).hexdigest() == GUARD_BODY_MD5


def test_the_table_list_appears_once_and_is_exactly_the_27_named_tables_in_order():
    code = _code(_M1275)
    arr = re.findall(r"tables text\[\] := ARRAY\[(.*?)\];", code, re.S)
    assert len(arr) == 1
    assert re.findall(r"'([a-z_]+)'", arr[0]) == TABLES and len(TABLES) == 27
    for t in TABLES:
        assert code.count(f"'{t}'") == 1, f"{t} must appear only in the list"


def test_excluded_tables_never_appear_in_the_executable_sql():
    code = _code(_M1275)
    for t in ("mimamsa_preferences", "mimamsa_negative_controls", "mimamsa_signal_families",
              "brahma_mimamsa_prediction_ledger", "brahma_prospective_ledger", "__ssv_", "chart_facts", "bodha_"):
        assert t not in code, t


def test_the_relink_list_is_exactly_the_pool_table_with_the_exact_old_definition():
    code = _code(_M1275)
    arr = re.findall(r"relink text\[\] := ARRAY\[(.*?)\];", code, re.S)
    assert len(arr) == 1 and re.findall(r"'([a-z_]+)'", arr[0]) == RELINK
    assert "relink_old constant text := 'FOREIGN KEY (chart_id) REFERENCES charts(id)'" in code
    assert code.count("DROP CONSTRAINT") == 1, "the only drop is the relink's"
    assert code.index("EXECUTE format('ALTER TABLE public.%I DROP CONSTRAINT") < code.index("EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT"), "drop first, then add"


def test_constraints_only_no_db_object_no_data_no_grant_no_transaction_control():
    code = _code(_M1275)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", code, re.M)
    assert not re.search(r"\b(CREATE\s+(OR\s+REPLACE\s+)?(VIEW|FUNCTION|TABLE|INDEX|TRIGGER|SCHEMA|EXTENSION)|INSERT INTO|UPDATE\s+\w+\s+SET|DELETE FROM|TRUNCATE|GRANT|REVOKE|DROP\s(?!CONSTRAINT))", code, re.I)
    assert code.count("EXECUTE format('ALTER TABLE") == 2 and "NOT VALID" not in code
    assert "FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE" in code
    assert "SET NULL" not in code


def test_guards_and_post_checks_are_present():
    code = _code(_M1275)
    for needle in ("does not exist", "is not an ordinary table", "ADD CONSTRAINT needs ownership", "owner-path item",
                   "pg_has_role(current_user, owner, 'USAGE')", "has no chart_id column", "will not invent a derivation",
                   "chart_id is nullable", "has no charts row; report, do not backfill", "is not the expected chart link",
                   "is missing, not validated, not ON DELETE CASCADE", "c.convalidated AND c.confdeltype = 'c'",
                   "something else changed", "$runs$", "r.state NOT IN ('completed', 'failed', 'stopped')", "active build run(s)",
                   "primary key not found"):
        assert needle in code, needle


def test_header_states_the_gap_the_list_the_exclusions_the_1265_requirement_locks_and_what_is_not_done():
    sql = _flat(_M1275)
    for needle in ("PRIVACY GAP", "N-108", "LAND TOGETHER WITH 1265", "THE GAP", "THE 27", "owned by amjis_app", "EXCLUDED",
                   "THE RELINK", "mimamsa_pool_contributions", "NO ACTION -> CASCADE", "__ssv_20260728a/b", "NULLABLE", "brahma_mimamsa_prediction_ledger",
                   "OWNER-PATH", "THE 1265 REQUIREMENT", "NOT EXISTS (SELECT 1 FROM public.charts WHERE id = OLD.chart_id)",
                   "pg_trigger_depth() is NOT a safe discriminator", "session_replication_role = replica", "ORDER / LOCKS",
                   "SHARE ROW EXCLUSIVE", "ACTIVE RUNS (ENFORCED", "SERVING EFFECT AT APPLY: none", "NOT DONE HERE",
                   "VERIFICATION BY PRODUCTION STRUCTURE", "ROLLBACK", "HELD", "AFTER S-L1", "on SS's review",
                   "chart-delete route", "charts/[id]/route.ts:87-107"):
        assert needle in sql, f"header no longer states: {needle}"


def test_number_and_name_follow_the_pattern_and_are_free_of_siblings():
    assert _M1275.name.startswith("1275_") and len(list(_MIG.glob("1275_*.sql"))) == 1
    assert 1200 <= int(_M1275.name[:4]) <= 1299


# -- LIVE tier: disposable PostgreSQL ------------------------------------------------

def _bin_dirs() -> list[Path]:
    cands: list[Path] = []
    for env in ("PG_BINS", "PG_BIN"):
        for p in os.environ.get(env, "").split(os.pathsep):
            if p:
                cands.append(Path(p))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    seen, out = set(), []
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists() and str(c.resolve()) not in seen:
            seen.add(str(c.resolve()))
            out.append(c)
    return out


def _versions() -> list[Path | None]:
    dirs = _bin_dirs()
    if os.environ.get("PG_BINS"):
        return dirs or [None]
    return dirs[:1] or [None]


@pytest.fixture(scope="module", params=_versions(), ids=lambda p: "nopg" if p is None else p.parent.name)
def pg_cluster(request):
    psycopg = pytest.importorskip("psycopg")
    binp = request.param
    if binp is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries and REQUIRE_PG_BINARIES=1")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1275pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m75", dir="/tmp"))  # unix socket paths are length-limited
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"],
                   check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses='' -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        with psycopg.connect(host=str(sockdir), port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            for r in ("amjis_app LOGIN", "data_plane_schema_owner NOLOGIN", "other_owner LOGIN", "app_writer LOGIN",
                      "attacker LOGIN", "consent_sweeper LOGIN"):
                c.execute(f"CREATE ROLE {r}")
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg, "major": binp.parent.name}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect(user="postgres", **kw):
        return psycopg.connect(host=sock, port=port, user=user, dbname=name, **kw)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _apply(connect, sql: str, notices: list[str] | None = None, user: str = "amjis_app"):
    """Run a migration the way migrate.ts does (one transaction around the whole file), AS amjis_app: it owns the tables and
    has NO CREATE privilege on schema public."""
    conn = connect(user=user)
    try:
        if notices is not None:
            conn.add_notice_handler(lambda d: notices.append(d.message_primary or ""))
        conn.execute(sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _exec(connect, sql: str, params=None, user: str = "postgres"):
    with connect(user=user) as c:
        c.execute(sql, params)


def _q(connect, sql: str, params=None, user: str = "postgres"):
    with connect(user=user) as c:
        return c.execute(sql, params).fetchall()


_PRED_DDL = """
CREATE TABLE mimamsa_predictions (
    chart_id uuid NOT NULL, prediction_id text NOT NULL, source_pramana_id text NOT NULL, outcome_claim text NOT NULL,
    domain text NOT NULL, observation_window daterange NOT NULL, eval_date date NOT NULL, confidence_band numrange NOT NULL,
    magnitude_expected text NOT NULL, falsifier_jsonb jsonb NOT NULL, base_rate numeric, emitted_at timestamptz NOT NULL,
    lifecycle_status text NOT NULL, driving_signals jsonb NOT NULL, frozen_bundle_hash text NOT NULL,
    bundle_formula_version text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), contact_id text,
    chart_context_stale_at timestamptz, chart_context_stale_reason text,
    chart_context_superseded_by_run_id uuid,
    PRIMARY KEY (chart_id, prediction_id),
    CONSTRAINT mimamsa_predictions_stale_pair_check CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL))
);
CREATE INDEX mimamsa_predictions_chart_idx ON mimamsa_predictions (chart_id);
"""
_BASE_DDL = """
CREATE TABLE charts (id uuid PRIMARY KEY, name text);
CREATE TABLE build_runs (id bigserial PRIMARY KEY, chart_id uuid REFERENCES charts(id), state text NOT NULL);
CREATE TABLE build_run_assets (run_id bigint NOT NULL REFERENCES build_runs(id), asset_id text NOT NULL);
CREATE TABLE chart_subject_consent (id bigserial PRIMARY KEY, chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE, consent_state text NOT NULL);
CREATE TABLE chart_subject_deletion_disputes (id bigserial PRIMARY KEY, chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE, status text NOT NULL);
"""


def _generic(t: str) -> str:
    return (f"CREATE TABLE {t} (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, payload text);\n"
            f"CREATE INDEX {t}_chart_idx ON {t} (chart_id);\n")


def _ddl() -> str:
    parts = [_BASE_DDL]
    for t in TABLES:
        if t == "mimamsa_predictions":
            parts.append(_PRED_DDL)
        elif t == "phala_muhurta":
            parts.append(_generic(t))
        elif t == "phala_mitigation":
            parts.append("CREATE TABLE phala_mitigation (id bigserial PRIMARY KEY, chart_id uuid NOT NULL, payload text,\n"
                         "  initiation_muhurta_ref bigint REFERENCES phala_muhurta(id) ON DELETE SET NULL);\n"
                         "CREATE INDEX phala_mitigation_chart_idx ON phala_mitigation (chart_id);\n")
        else:
            parts.append(_generic(t))
    parts.append("CREATE TABLE mimamsa_pool_contributions (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL,\n"
                 "  payload text, CONSTRAINT mimamsa_pool_contributions_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id));\n"
                 "CREATE INDEX mimamsa_pool_contributions_chart_idx ON mimamsa_pool_contributions (chart_id);\n")
    return "\n".join(parts)


def _mirror_production(c):
    c.execute("ALTER SCHEMA public OWNER TO data_plane_schema_owner")
    c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
    c.execute("GRANT USAGE ON SCHEMA public TO amjis_app, app_writer, attacker, consent_sweeper, other_owner")
    for (t,) in c.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall():
        c.execute(f'ALTER TABLE public."{t}" OWNER TO amjis_app')
    for (sq,) in c.execute("SELECT sequencename FROM pg_sequences WHERE schemaname = 'public'").fetchall():
        c.execute(f'ALTER SEQUENCE public."{sq}" OWNER TO amjis_app')


def _make_fixture(connect, *, extra_ddl: str = ""):
    with connect() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")  # scenarios reuse one database
        c.execute(_ddl())
        if extra_ddl:
            c.execute(extra_ddl)
        _mirror_production(c)
        c.commit()


def _insert_pred(c, chart: str, pid: str, status: str = "pending"):
    c.execute("INSERT INTO mimamsa_predictions (chart_id, prediction_id, source_pramana_id, outcome_claim, domain, observation_window, "
              "eval_date, confidence_band, magnitude_expected, falsifier_jsonb, emitted_at, lifecycle_status, driving_signals, "
              "frozen_bundle_hash, bundle_formula_version) VALUES (%s, %s, 'src', 'claim', 'career', '[2026-11-01,2026-12-01)', "
              "'2026-12-01', '[0.2,0.8]', 'm', '{}', now(), %s, '[]', 'h', 'v1')", (chart, pid, status))


def _seed(connect, rows: int = 2):
    """Charts A and B, `rows` rows per chart in every one of the 27 tables (predictions: pending and confirmed), consent rows."""
    with connect() as c:
        c.execute("INSERT INTO charts VALUES (%s, 'A'), (%s, 'B')", (CHART_A, CHART_B))
        for chart in (CHART_A, CHART_B):
            for t in ALL_TABLES:
                if t == "mimamsa_predictions":
                    for k in range(rows):
                        _insert_pred(c, chart, f"p{k}", "pending" if k % 2 == 0 else "confirmed")
                elif t == "phala_mitigation":
                    mid = c.execute("INSERT INTO phala_muhurta (chart_id, payload) VALUES (%s, 'x') RETURNING id", (chart,)).fetchone()[0]
                    for k in range(rows):
                        c.execute("INSERT INTO phala_mitigation (chart_id, payload, initiation_muhurta_ref) VALUES (%s, 'x', %s)", (chart, mid))
                else:
                    for k in range(rows):
                        c.execute(f"INSERT INTO {t} (chart_id, payload) VALUES (%s, 'x')", (chart,))
            c.execute("INSERT INTO chart_subject_consent (chart_id, consent_state) VALUES (%s, 'granted')", (chart,))
            c.execute("INSERT INTO build_runs (chart_id, state) VALUES (%s, 'completed')", (chart,))
        c.commit()


def _fk_defs(connect):
    return dict(_q(connect, "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                            "WHERE contype='f' AND connamespace='public'::regnamespace ORDER BY 1"))


def _chart_counts(connect, chart):
    return {t: _q(connect, f"SELECT count(*) FROM {t} WHERE chart_id = %s", (chart,))[0][0] for t in ALL_TABLES}


def _data_digest(connect):
    return {t: _q(connect, f"SELECT md5(coalesce(string_agg(to_jsonb(x)::text, '|' ORDER BY to_jsonb(x)::text), '')) FROM {t} x")[0][0] for t in ALL_TABLES}


def _route_delete(connect, chart: str, user: str = "amjis_app"):
    """The statements of platform/src/app/api/charts/[id]/route.ts:87-107 that touch the tables in this fixture, in order,
    in one transaction: build_runs of the chart first, then the charts row (everything else is left to the cascades)."""
    conn = connect(user=user)
    try:
        conn.execute("DELETE FROM build_run_assets WHERE run_id IN (SELECT id FROM build_runs WHERE chart_id = %s)", (chart,))
        conn.execute("DELETE FROM build_runs WHERE chart_id = %s", (chart,))
        conn.execute("DELETE FROM charts WHERE id = %s", (chart,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# -- the 1265 guard in three variants ----------------------------------------------------

_DISC_NOTEXISTS = """
  -- DELETE caused by deleting the chart itself (the RI cascade of charts): the parent row is already gone.
  IF NOT EXISTS (SELECT 1 FROM public.charts h WHERE h.id = OLD.chart_id) THEN
    RAISE LOG 'mimamsa_predictions_frozen_row_guard: DELETE authorized by chart deletion; chart_id=%, prediction_id=%', OLD.chart_id, OLD.prediction_id;
    RETURN OLD;
  END IF;
"""
_DISC_DEPTH = """
  IF pg_trigger_depth() > 1 THEN
    RETURN OLD;
  END IF;
"""
_ANCHOR = "  -- DELETE. The one exception:"


def _guard_sql(variant: str) -> str:
    body = _GUARD_BODY.read_text()
    assert _ANCHOR in body
    if variant == "notexists":
        body = body.replace(_ANCHOR, _DISC_NOTEXISTS + _ANCHOR, 1)
    elif variant == "depth":
        body = body.replace(_ANCHOR, _DISC_DEPTH + _ANCHOR, 1)
    elif variant != "head":
        raise ValueError(variant)
    return f"""
CREATE FUNCTION public.mimamsa_predictions_frozen_row_guard() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER
  SET search_path = pg_catalog, pg_temp AS $frozen${body}$frozen$;
CREATE TRIGGER mimamsa_predictions_frozen_row_guard BEFORE UPDATE OR DELETE ON public.mimamsa_predictions
  FOR EACH ROW EXECUTE FUNCTION public.mimamsa_predictions_frozen_row_guard();
CREATE TRIGGER mimamsa_predictions_frozen_row_guard_truncate BEFORE TRUNCATE ON public.mimamsa_predictions
  FOR EACH STATEMENT EXECUTE FUNCTION public.mimamsa_predictions_frozen_row_guard();
ALTER TABLE public.mimamsa_predictions ENABLE ALWAYS TRIGGER mimamsa_predictions_frozen_row_guard;
ALTER TABLE public.mimamsa_predictions ENABLE ALWAYS TRIGGER mimamsa_predictions_frozen_row_guard_truncate;
"""


def _install_guard(connect, variant: str):
    """Install the guard the way 1265's protected window does (postgres admin transiently holding CREATE), leaving ownership of the
    table with amjis_app."""
    _exec(connect, _guard_sql(variant))


# -- apply -------------------------------------------------------------------------------

def test_fixture_mirrors_production_amjis_app_has_usage_only_and_owns_every_table(db):
    _make_fixture(db)
    r = _q(db, "SELECT has_schema_privilege('amjis_app','public','CREATE'), has_schema_privilege('amjis_app','public','USAGE'), "
               "(SELECT count(*) FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r' AND relowner <> 'amjis_app'::regrole)")[0]
    assert r == (False, True, 0)


def test_precondition_before_apply_a_chart_delete_leaves_every_row_of_the_27_tables_behind(db):
    _make_fixture(db)
    _seed(db)
    _exec(db, "DELETE FROM mimamsa_pool_contributions")  # its NO ACTION link would block the delete: tested separately below
    before = _chart_counts(db, CHART_A)
    assert all(v > 0 for k, v in before.items() if k != "mimamsa_pool_contributions")
    _route_delete(db, CHART_A)
    assert _chart_counts(db, CHART_A) == before, "precondition: nothing reaches these tables today (the privacy gap)"


def test_precondition_the_existing_no_action_pool_link_BLOCKS_a_chart_delete_once_it_holds_a_row(db):
    """SS N-108 addendum: mimamsa_pool_contributions has an ON DELETE NO ACTION link; with a row it makes DELETE FROM charts fail."""
    _make_fixture(db)
    _seed(db)
    assert _q(db, "SELECT count(*) FROM mimamsa_pool_contributions WHERE chart_id = %s", (CHART_A,))[0][0] == 2
    with pytest.raises(Exception) as ei:
        _route_delete(db, CHART_A)
    assert "mimamsa_pool_contributions_chart_id_fkey" in str(ei.value), str(ei.value)
    assert _q(db, "SELECT count(*) FROM charts WHERE id = %s", (CHART_A,))[0][0] == 1


def test_the_relink_replaces_the_no_action_link_with_cascade_in_one_step_and_a_pool_row_is_deleted_with_its_chart(db):
    _make_fixture(db)
    _seed(db)
    assert _fk_defs(db)[POOL_CON] == OLD_POOL_DEF
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert _fk_defs(db)[POOL_CON] == EXPECTED_DEF
    assert _q(db, "SELECT convalidated, confdeltype::text, condeferrable FROM pg_constraint WHERE conname = %s", (POOL_CON,)) == [(True, "c", False)]
    assert any("replacing a NO ACTION link" in n for n in notices)
    b_rows = _q(db, "SELECT count(*) FROM mimamsa_pool_contributions WHERE chart_id = %s", (CHART_B,))[0][0]
    _route_delete(db, CHART_A)
    assert _q(db, "SELECT count(*) FROM mimamsa_pool_contributions WHERE chart_id = %s", (CHART_A,))[0][0] == 0
    assert _q(db, "SELECT count(*) FROM mimamsa_pool_contributions WHERE chart_id = %s", (CHART_B,))[0][0] == b_rows > 0


def test_the_relink_refuses_any_other_existing_definition_and_accepts_the_cascading_one(db):
    for other in ("ON DELETE SET NULL", "ON DELETE RESTRICT"):
        _make_fixture(db)
        _exec(db, f"ALTER TABLE mimamsa_pool_contributions DROP CONSTRAINT {POOL_CON}; "
                  f"ALTER TABLE mimamsa_pool_contributions ADD CONSTRAINT {POOL_CON} FOREIGN KEY (chart_id) REFERENCES charts(id) {other}")
        before = _fk_defs(db)
        with pytest.raises(Exception) as ei:
            _apply(db, _REAL)
        assert "is not the expected chart link" in str(ei.value), str(ei.value)
        assert _fk_defs(db) == before
    _make_fixture(db)
    _exec(db, f"ALTER TABLE mimamsa_pool_contributions DROP CONSTRAINT {POOL_CON}; "
              f"ALTER TABLE mimamsa_pool_contributions ADD CONSTRAINT {POOL_CON} FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE")
    _apply(db, _REAL)  # already cascading: accepted, nothing dropped
    assert _fk_defs(db)[POOL_CON] == EXPECTED_DEF
    _make_fixture(db)
    _exec(db, f"ALTER TABLE mimamsa_pool_contributions DROP CONSTRAINT {POOL_CON}")  # absent: added
    _apply(db, _REAL)
    assert _fk_defs(db)[POOL_CON] == EXPECTED_DEF


def test_the_relink_checks_the_pool_table_like_the_others(db):
    _make_fixture(db)
    _exec(db, "ALTER TABLE mimamsa_pool_contributions ALTER COLUMN chart_id DROP NOT NULL")
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "public.mimamsa_pool_contributions.chart_id is nullable" in str(ei.value)
    _make_fixture(db)
    _exec(db, "ALTER TABLE mimamsa_pool_contributions OWNER TO other_owner")
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "mimamsa_pool_contributions" in str(ei.value) and "owner-path item" in str(ei.value)


def test_apply_adds_exactly_the_27_links_and_changes_no_data_column_or_index(db):
    _make_fixture(db)
    _seed(db)
    fks_before, data_before = _fk_defs(db), _data_digest(db)
    idx_before = _q(db, "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY 1, 2")
    notices: list[str] = []
    _apply(db, _REAL, notices)
    fks_after = _fk_defs(db)
    assert set(fks_after) - set(fks_before) == set(CONS) and set(fks_before) <= set(fks_after)
    assert len(fks_after) == len(fks_before) + 27
    assert all(fks_after[c] == EXPECTED_DEF for c in CONS)
    assert fks_before[POOL_CON] == OLD_POOL_DEF and fks_after[POOL_CON] == EXPECTED_DEF, "the relink took"
    assert {k: fks_after[k] for k in fks_before if k != POOL_CON} == {k: v for k, v in fks_before.items() if k != POOL_CON}, "another existing FK changed"
    assert _data_digest(db) == data_before
    assert _q(db, "SELECT tablename, indexname, indexdef FROM pg_indexes WHERE schemaname='public' ORDER BY 1, 2") == idx_before
    assert _q(db, "SELECT count(*) FROM pg_proc WHERE pronamespace='public'::regnamespace")[0][0] == 0, "no function created"
    rows = _q(db, "SELECT convalidated, confdeltype::text, condeferrable FROM pg_constraint WHERE conname = ANY(%s)", (CONS,))
    assert len(rows) == 27 and set(rows) == {(True, "c", False)}


def test_the_delete_route_scenario_without_a_guard_every_row_of_the_chart_is_gone_in_all_27_tables_other_chart_untouched(db):
    _make_fixture(db)
    _seed(db)
    b_before = _chart_counts(db, CHART_B)
    _apply(db, _REAL)
    assert all(v > 0 for v in _chart_counts(db, CHART_A).values())
    _route_delete(db, CHART_A)
    assert _chart_counts(db, CHART_A) == {t: 0 for t in ALL_TABLES}
    assert _chart_counts(db, CHART_B) == b_before
    assert _q(db, "SELECT count(*) FROM chart_subject_consent WHERE chart_id = %s", (CHART_A,))[0][0] == 0
    assert _q(db, "SELECT count(*) FROM phala_mitigation WHERE chart_id = %s", (CHART_B,))[0][0] > 0, "SET NULL link between phala tables untouched"


def test_a_row_with_a_missing_chart_is_refused_on_every_one_of_the_27_after_apply(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    ghost = "11111111-2222-4333-8444-555555555555"
    for t in TABLES:
        with pytest.raises(Exception) as ei:
            with db() as c:
                if t == "mimamsa_predictions":
                    _insert_pred(c, ghost, "ghost")
                else:
                    c.execute(f"INSERT INTO {t} (chart_id) VALUES (%s)", (ghost,))
        assert f"{t}_chart_id_fkey" in str(ei.value), t


def test_idempotent_second_run_changes_nothing(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    snap = (_fk_defs(db), _data_digest(db))
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert sum("already present on" in n for n in notices) == 28
    assert snap == (_fk_defs(db), _data_digest(db))


def test_partial_state_adds_only_the_remaining(db):
    _make_fixture(db)
    _exec(db, "ALTER TABLE phala_muhurta ADD CONSTRAINT phala_muhurta_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE")
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert set(CONS) <= set(_fk_defs(db)) and sum("already present on" in n for n in notices) == 1


# -- guards ---------------------------------------------------------------------------------

def test_stop_when_a_table_lacks_chart_id_is_nullable_or_holds_a_missing_chart(db):
    for t in ("phala_phaladesa", "mimamsa_attribution", "mimamsa_predictions"):
        _make_fixture(db)
        _exec(db, f"ALTER TABLE {t} DROP COLUMN chart_id CASCADE")
        before = _fk_defs(db)
        with pytest.raises(Exception) as ei:
            _apply(db, _REAL)
        assert f"public.{t} has no chart_id column; cannot add the ownership link and will not invent a derivation" in str(ei.value), str(ei.value)
        assert _fk_defs(db) == before
    for t in ("phala_muhurta", "mimamsa_fact_adjustment"):
        _make_fixture(db)
        _exec(db, f"ALTER TABLE {t} ALTER COLUMN chart_id DROP NOT NULL")
        with pytest.raises(Exception) as ei:
            _apply(db, _REAL)
        assert f"public.{t}.chart_id is nullable" in str(ei.value), str(ei.value)
    for t in ("phala_mitigation", "mimamsa_signal_adjustment", "mimamsa_journal"):
        _make_fixture(db)
        _exec(db, f"INSERT INTO {t} (chart_id) VALUES ('99999999-0000-4000-8000-000000000001')")
        before = _fk_defs(db)
        with pytest.raises(Exception) as ei:
            _apply(db, _REAL)
        assert f"public.{t} holds 1 row(s) whose chart_id has no charts row; report, do not backfill" in str(ei.value), str(ei.value)
        assert _fk_defs(db) == before


def test_a_table_owned_by_another_role_is_an_owner_path_item_and_changes_nothing(db):
    _make_fixture(db)
    _exec(db, "ALTER TABLE mimamsa_signal_adjustment OWNER TO other_owner")
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "mimamsa_signal_adjustment" in str(ei.value) and "owner-path item" in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before


def test_guard_refuses_an_existing_link_that_is_not_the_expected_definition(db):
    _make_fixture(db)
    _exec(db, "ALTER TABLE mimamsa_discoveries ADD CONSTRAINT mimamsa_discoveries_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id)")
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "is not the expected chart link" in str(ei.value), str(ei.value)


def test_guard_refuses_a_missing_table_and_a_missing_charts_pk(db):
    _make_fixture(db)
    _exec(db, "DROP TABLE mimamsa_reliability")
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "public.mimamsa_reliability does not exist" in str(ei.value)
    _make_fixture(db)
    _exec(db, "ALTER TABLE charts ADD COLUMN x int")  # PK intact -> must still apply
    _apply(db, _REAL)


@pytest.mark.parametrize("asset", ACTIVE_ASSETS)
@pytest.mark.parametrize("state", ["running", "planned", "paused"])
def test_active_build_run_guard_refuses_and_changes_nothing(db, asset, state):
    _make_fixture(db)
    _exec(db, "INSERT INTO build_runs (state) VALUES (%s)", (state,))
    _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), %s FROM build_runs", (asset,))
    before = _fk_defs(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "active build run" in str(ei.value) and asset in str(ei.value), str(ei.value)
    assert _fk_defs(db) == before


def test_finished_runs_and_runs_of_other_assets_do_not_block(db):
    _make_fixture(db)
    for st, aid in (("completed", "mi_bhavisya"), ("failed", "ph_muhurta"), ("stopped", "mi_kula"), ("running", "ga_vargas")):
        _exec(db, "INSERT INTO build_runs (state) VALUES (%s)", (st,))
        _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), %s FROM build_runs", (aid,))
    _apply(db, _REAL)
    assert set(CONS) <= set(_fk_defs(db))


def test_lock_timeout_fails_fast_when_a_target_table_is_locked(db):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE mimamsa_predictions IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = db(user="amjis_app", options="-c statement_timeout=20000")
        with pytest.raises(Exception) as ei:
            victim.execute(_REAL)
        elapsed = time.monotonic() - t0
        victim.rollback()
        victim.close()
    finally:
        blocker.rollback()
        blocker.close()
    assert "lock timeout" in str(ei.value).lower(), str(ei.value)
    assert elapsed < 15 and not (set(CONS) & set(_fk_defs(db)))


def test_production_sized_apply_is_fast(db):
    """Production-sized synthetic data in the two big tables (123k and 100k rows, 2 charts): the whole file, validation included."""
    _make_fixture(db)
    with db() as c:
        c.execute("INSERT INTO charts VALUES (%s, 'A'), (%s, 'B')", (CHART_A, CHART_B))
        c.execute("INSERT INTO mimamsa_fact_adjustment (chart_id, payload) SELECT (ARRAY[%s,%s])[1 + mod(g, 2)]::uuid, 'x' FROM generate_series(1, 123272) g", (CHART_A, CHART_B))
        c.execute("INSERT INTO mimamsa_signal_adjustment (chart_id, payload) SELECT (ARRAY[%s,%s])[1 + mod(g, 2)]::uuid, 'x' FROM generate_series(1, 100275) g", (CHART_A, CHART_B))
        c.execute("INSERT INTO phala_mitigation (chart_id, payload) SELECT %s::uuid, 'x' FROM generate_series(1, 1277) g", (CHART_A,))
        c.commit()
    t0 = time.monotonic()
    _apply(db, _REAL)
    elapsed = time.monotonic() - t0
    print(f"\n1275 apply on production-sized data: {elapsed:.3f}s")
    assert elapsed < 30
    t0 = time.monotonic()
    _route_delete(db, CHART_A)
    print(f"chart delete cascading {123272 // 2 + 100275 // 2 + 1277} rows: {time.monotonic() - t0:.3f}s")
    assert _chart_counts(db, CHART_A)["mimamsa_fact_adjustment"] == 0


# -- THE 1265 PART ---------------------------------------------------------------------------

def _prediction_rows(connect, chart):
    return _q(connect, "SELECT count(*) FROM mimamsa_predictions WHERE chart_id = %s", (chart,))[0][0]


def test_1265_head_as_it_stands_REFUSES_the_chart_delete_so_it_must_change(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _install_guard(db, "head")
    before = _chart_counts(db, CHART_A)
    with pytest.raises(Exception) as ei:
        _route_delete(db, CHART_A)
    assert "mimamsa_predictions_frozen_row_guard: frozen predictions cannot be deleted" in str(ei.value), str(ei.value)
    assert _chart_counts(db, CHART_A) == before, "the whole route transaction rolled back, nothing lost"
    assert _q(db, "SELECT count(*) FROM charts WHERE id = %s", (CHART_A,))[0][0] == 1


@pytest.mark.parametrize("variant", ["notexists"])
def test_chart_delete_with_the_guard_removes_all_rows_in_every_table_and_a_direct_delete_stays_refused(db, variant):
    """BOTH IN ONE FIXTURE (SS N-108): the chart delete removes all the chart's rows in all 27 tables including its predictions;
    a direct DELETE on a prediction is refused for every role -- app writer, table owner and superuser; the other chart is untouched."""
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _install_guard(db, variant)
    _exec(db, "GRANT SELECT, INSERT, UPDATE, DELETE ON mimamsa_predictions TO app_writer")
    _exec(db, "GRANT SELECT ON charts TO app_writer")
    b_before = _chart_counts(db, CHART_B)
    # a direct DELETE of a prediction (pending AND confirmed) of the chart that is about to be deleted, by each role: refused
    for user in ("app_writer", "amjis_app", "postgres"):
        for pid in ("p0", "p1"):
            with pytest.raises(Exception) as ei:
                _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = %s", (CHART_A, pid), user=user)
            assert "frozen predictions cannot be deleted" in str(ei.value), (user, pid, str(ei.value))
    with pytest.raises(Exception) as ei:
        _exec(db, "DELETE FROM mimamsa_predictions", user="postgres")
    assert "frozen predictions cannot be deleted" in str(ei.value)
    with pytest.raises(Exception) as ei:
        _exec(db, "TRUNCATE mimamsa_predictions", user="postgres")
    assert "TRUNCATE" in str(ei.value)
    with pytest.raises(Exception) as ei:
        _exec(db, "UPDATE mimamsa_predictions SET outcome_claim = 'changed' WHERE chart_id = %s", (CHART_A,), user="amjis_app")
    assert "frozen column(s) outcome_claim cannot be updated" in str(ei.value)
    assert _prediction_rows(db, CHART_A) == 2
    # the chart itself is deleted (the route's statements): everything of that chart goes
    _route_delete(db, CHART_A)
    assert _chart_counts(db, CHART_A) == {t: 0 for t in ALL_TABLES}
    assert _prediction_rows(db, CHART_A) == 0
    assert _chart_counts(db, CHART_B) == b_before, "the other chart was touched"
    # and after the chart delete a direct DELETE on the OTHER chart's prediction is still refused
    with pytest.raises(Exception) as ei:
        _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), user="amjis_app")
    assert "frozen predictions cannot be deleted" in str(ei.value)
    assert _prediction_rows(db, CHART_B) == 2


def test_chart_delete_that_rolls_back_leaves_every_prediction(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _install_guard(db, "notexists")
    conn = db(user="amjis_app")
    conn.execute("DELETE FROM build_runs WHERE chart_id = %s", (CHART_A,))
    conn.execute("DELETE FROM charts WHERE id = %s", (CHART_A,))
    assert conn.execute("SELECT count(*) FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,)).fetchone()[0] == 0, "visible inside the txn"
    conn.rollback()
    conn.close()
    assert _prediction_rows(db, CHART_A) == 2


def test_the_consent_withdrawal_exception_of_1265_still_works_alongside_the_discriminator(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _install_guard(db, "notexists")
    _exec(db, "UPDATE chart_subject_consent SET consent_state = 'withdrawn' WHERE chart_id = %s", (CHART_A,))
    _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,), user="amjis_app")
    assert _prediction_rows(db, CHART_A) == 0 and _prediction_rows(db, CHART_B) == 2
    _exec(db, "INSERT INTO chart_subject_deletion_disputes (chart_id, status) VALUES (%s, 'open')", (CHART_B,))
    _exec(db, "UPDATE chart_subject_consent SET consent_state = 'withdrawn' WHERE chart_id = %s", (CHART_B,))
    with pytest.raises(Exception) as ei:
        _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), user="amjis_app")
    assert "frozen predictions cannot be deleted" in str(ei.value), "an open dispute still blocks"


_DECOY = """
DROP SCHEMA IF EXISTS atk CASCADE;
CREATE SCHEMA atk AUTHORIZATION attacker;
CREATE TABLE atk.decoy (id int);
CREATE FUNCTION atk.fire() RETURNS trigger LANGUAGE plpgsql AS $f$
BEGIN
  DELETE FROM public.mimamsa_predictions WHERE chart_id = '%s';
  RETURN NEW;
END $f$;
ALTER FUNCTION atk.fire() OWNER TO attacker;
CREATE TRIGGER decoy_fire AFTER INSERT ON atk.decoy FOR EACH ROW EXECUTE FUNCTION atk.fire();
ALTER TABLE atk.decoy OWNER TO attacker;
GRANT USAGE ON SCHEMA atk TO attacker;
GRANT SELECT, DELETE ON public.mimamsa_predictions TO attacker;
GRANT SELECT ON public.charts TO attacker;
""" % CHART_A


def test_the_trigger_depth_discriminator_CAN_be_spoofed_by_a_role_that_may_create_a_trigger_the_not_exists_one_cannot(db):
    """Same attack, two discriminators. The attacker holds DELETE on mimamsa_predictions, owns a decoy table with an AFTER INSERT
    trigger that issues the direct DELETE; inside that nested call pg_trigger_depth() is 2, exactly what the RI cascade shows."""
    outcome = {}
    for variant in ("depth", "notexists"):
        _make_fixture(db)
        _seed(db)
        _apply(db, _REAL)
        _install_guard(db, variant)
        _exec(db, _DECOY)
        try:
            _exec(db, "INSERT INTO atk.decoy VALUES (1)", user="attacker")
            outcome[variant] = f"DELETED {2 - _prediction_rows(db, CHART_A)} frozen rows via the decoy trigger"
        except Exception as exc:  # noqa: BLE001
            outcome[variant] = "REFUSED: " + str(exc).splitlines()[0][:90]
            assert _prediction_rows(db, CHART_A) == 2
    print("\nspoof attempt:", outcome)
    assert outcome["depth"].startswith("DELETED 2"), outcome
    assert outcome["notexists"].startswith("REFUSED"), outcome


def test_the_depth_discriminator_also_lets_the_RI_cascade_through_so_both_work_for_the_legit_path_only_not_exists_resists_spoofing(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _install_guard(db, "depth")
    _route_delete(db, CHART_A)
    assert _prediction_rows(db, CHART_A) == 0


def test_pg_trigger_depth_inside_the_guard_is_2_for_the_cascade_and_1_for_a_direct_delete(db):
    """The measurement behind the spoof: depth is the same for the RI cascade and for a nested call from any trigger."""
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "CREATE TABLE depth_log (op text, depth int); GRANT INSERT ON depth_log TO PUBLIC;\n"
              "CREATE FUNCTION log_depth() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN INSERT INTO depth_log VALUES (TG_OP, pg_trigger_depth()); RETURN OLD; END $f$;\n"
              "CREATE TRIGGER log_depth BEFORE DELETE ON mimamsa_predictions FOR EACH ROW EXECUTE FUNCTION log_depth()")
    _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'p0'", (CHART_B,), user="amjis_app")
    direct = _q(db, "SELECT depth FROM depth_log")[0][0]
    _exec(db, "TRUNCATE depth_log")
    _route_delete(db, CHART_A)
    cascade = {r[0] for r in _q(db, "SELECT depth FROM depth_log")}
    assert direct == 1 and cascade == {2}


def test_not_exists_sees_the_parent_gone_only_inside_the_cascade_and_never_for_a_direct_delete(db):
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _exec(db, "CREATE TABLE seen (chart_exists boolean, via text); GRANT INSERT ON seen TO PUBLIC;\n"
              "CREATE FUNCTION log_seen() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN INSERT INTO seen VALUES "
              "(EXISTS (SELECT 1 FROM public.charts h WHERE h.id = OLD.chart_id), TG_OP); RETURN OLD; END $f$;\n"
              "CREATE TRIGGER log_seen BEFORE DELETE ON mimamsa_predictions FOR EACH ROW EXECUTE FUNCTION log_seen()")
    _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s AND prediction_id = 'p0'", (CHART_B,), user="amjis_app")
    direct = _q(db, "SELECT chart_exists FROM seen")
    _exec(db, "TRUNCATE seen")
    _route_delete(db, CHART_A)
    cascade = {r[0] for r in _q(db, "SELECT chart_exists FROM seen")}
    assert direct == [(True,)] and cascade == {False}


def test_the_only_way_to_make_not_exists_true_outside_the_cascade_needs_superuser_and_is_also_a_way_to_disable_the_guard(db):
    """Limit stated: session_replication_role = replica skips RI triggers, so a superuser can delete the charts row without the
    cascade and then delete predictions directly. A non-superuser cannot set it; a superuser can equally DISABLE the trigger."""
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _install_guard(db, "notexists")
    with pytest.raises(Exception) as ei:
        with db(user="amjis_app") as c:
            c.execute("SET session_replication_role = replica")
    assert "permission denied to set parameter" in str(ei.value) or "must be superuser" in str(ei.value)
    with db() as c:  # superuser
        c.execute("SET session_replication_role = replica")
        c.execute("DELETE FROM charts WHERE id = %s", (CHART_A,))  # no cascade (RI skipped)
        c.commit()
    assert _prediction_rows(db, CHART_A) == 2, "the cascade did not run"
    _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_A,), user="amjis_app")  # orphan rows (their chart is gone) can go
    assert _prediction_rows(db, CHART_A) == 0
    with pytest.raises(Exception):
        _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), user="amjis_app")


def test_a_non_owner_non_superuser_with_delete_cannot_spoof_by_inserting_a_chart_then_deleting_it(db):
    """Creating and deleting THEIR OWN chart only reaches their own chart's rows; they cannot make another chart's parent 'gone'."""
    _make_fixture(db)
    _seed(db)
    _apply(db, _REAL)
    _install_guard(db, "notexists")
    _exec(db, "GRANT SELECT, INSERT, DELETE ON charts TO attacker; GRANT SELECT, DELETE ON mimamsa_predictions TO attacker")
    _exec(db, "INSERT INTO charts VALUES (gen_random_uuid(), 'mine')", user="attacker")
    with pytest.raises(Exception) as ei:
        _exec(db, "DELETE FROM mimamsa_predictions WHERE chart_id = %s", (CHART_B,), user="attacker")
    assert "frozen predictions cannot be deleted" in str(ei.value)


# -- MUTATION proof --------------------------------------------------------------------------

def _scenario(db, sql: str) -> list[str]:
    """Violations of the contract when `sql` (a possibly mutated migration) is applied, as amjis_app, to a fresh seeded fixture."""
    v: list[str] = []
    _make_fixture(db)
    _seed(db)
    fks_before, data_before = _fk_defs(db), _data_digest(db)
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"apply failed: {str(exc).splitlines()[0]}"]
    fks_after = _fk_defs(db)
    for c in CONS + [POOL_CON]:
        if fks_after.get(c) != EXPECTED_DEF:
            v.append(f"chart link {c} missing or wrong")
    if len(fks_after) != len(fks_before) + 27:
        v.append("FK count did not rise by exactly 27")
    if _data_digest(db) != data_before:
        v.append("a data row changed")
    b_before = _chart_counts(db, CHART_B)
    try:
        _route_delete(db, CHART_A)
    except Exception as exc:  # noqa: BLE001
        v.append(f"chart delete failed: {str(exc).splitlines()[0]}")
        return v
    left = {t: n for t, n in _chart_counts(db, CHART_A).items() if n}
    if left:
        v.append(f"chart deletion left rows behind: {sorted(left)}")
    if _chart_counts(db, CHART_B) != b_before:
        v.append("chart deletion touched another chart")
    return v


def _stop_scenario(db, sql: str) -> list[str]:
    v: list[str] = []
    for label, setup, message in (
            ("no chart_id", "ALTER TABLE mimamsa_attribution DROP COLUMN chart_id CASCADE", "has no chart_id column"),
            ("nullable chart_id", "ALTER TABLE phala_muhurta ALTER COLUMN chart_id DROP NOT NULL", "chart_id is nullable"),
            ("missing chart", "INSERT INTO mimamsa_journal (chart_id) VALUES ('99999999-0000-4000-8000-000000000001')", "has no charts row; report, do not backfill"),
            ("not the owner", "ALTER TABLE mimamsa_signal_adjustment OWNER TO other_owner", "owner-path item")):
        _make_fixture(db)
        _exec(db, setup)
        before = _fk_defs(db)
        try:
            _apply(db, sql)
            v.append(f"{label}: applied")
        except Exception as exc:  # noqa: BLE001
            if message not in str(exc):
                v.append(f"{label}: refused, but not by its own guard: {str(exc).splitlines()[0]}")
        if _fk_defs(db) != before:
            v.append(f"{label}: changed constraints while refusing")
    return v


def _redef_scenario(db, sql: str) -> list[str]:
    v: list[str] = []
    for setup in ("ALTER TABLE mimamsa_discoveries ADD CONSTRAINT mimamsa_discoveries_chart_id_fkey FOREIGN KEY (chart_id) REFERENCES charts(id)",
                  f"ALTER TABLE mimamsa_pool_contributions DROP CONSTRAINT {POOL_CON}; ALTER TABLE mimamsa_pool_contributions ADD CONSTRAINT {POOL_CON} "
                  "FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE SET NULL"):
        _make_fixture(db)
        _exec(db, setup)
        try:
            _apply(db, sql)
            v.append("accepted an existing link with another definition")
        except Exception as exc:  # noqa: BLE001
            if "is not the expected chart link" not in str(exc):
                v.append(f"refused for another reason: {str(exc).splitlines()[0]}")
    return v


def _runs_scenario(db, sql: str) -> list[str]:
    _make_fixture(db)
    _exec(db, "INSERT INTO build_runs (state) VALUES ('running')")
    _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) VALUES (1, 'mi_bhavisya')")
    try:
        _apply(db, sql)
        return ["applied during an active run"]
    except Exception as exc:  # noqa: BLE001
        return [] if "active build run" in str(exc) else [f"refused for another reason: {str(exc).splitlines()[0]}"]


def _lock_scenario(db, sql: str) -> list[str]:
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE mimamsa_predictions IN ACCESS EXCLUSIVE MODE")
    try:
        victim = db(user="amjis_app", options="-c statement_timeout=8000")
        try:
            victim.execute(sql)
            return ["did not fail while a target table was locked"]
        except Exception as exc:  # noqa: BLE001
            return [] if "lock timeout" in str(exc).lower() else [f"failed for another reason (no lock_timeout): {str(exc).splitlines()[0]}"]
        finally:
            victim.rollback()
            victim.close()
    finally:
        blocker.rollback()
        blocker.close()


_EXTRA = "    EXECUTE 'ALTER TABLE public.charts ADD COLUMN IF NOT EXISTS x int';\n"
_MUT_ANCHOR = "    -- Post-check: never trust a silent no-op."
_MUTANTS = {
    "list_missing_a_table": (_REAL.replace("        'mimamsa_signal_adjustment',\n", ""), "scenario"),
    "list_missing_phala_phaladesa": (_REAL.replace("        'phala_phaladesa',\n", ""), "scenario"),
    "add_pass_removed": (_REAL.replace("EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE', tbl, con);", "NULL;"), "scenario"),
    "link_without_cascade": (_REAL.replace("REFERENCES public.charts(id) ON DELETE CASCADE', tbl, con);", "REFERENCES public.charts(id)', tbl, con);"), "scenario"),
    "link_not_valid": (_REAL.replace("REFERENCES public.charts(id) ON DELETE CASCADE', tbl, con);", "REFERENCES public.charts(id) ON DELETE CASCADE NOT VALID', tbl, con);"), "scenario"),
    "link_set_null": (_REAL.replace("REFERENCES public.charts(id) ON DELETE CASCADE', tbl, con);", "REFERENCES public.charts(id) ON DELETE SET NULL', tbl, con);"), "scenario"),
    "relink_list_empty": (_REAL.replace("        'mimamsa_pool_contributions'\n", ""), "scenario"),
    "relink_drop_removed": (_REAL.replace("EXECUTE format('ALTER TABLE public.%I DROP CONSTRAINT %I', tbl, con);", "NULL;"), "scenario"),
    "relink_old_definition_widened_to_any": (_REAL.replace("AND NOT (tbl = ANY (relink) AND cdef = relink_old)", "AND NOT (tbl = ANY (relink))"), "redef"),
    "stop_no_chart_id_neutered": (_REAL.replace("IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'chart_id' AND NOT attisdropped) THEN", "IF false THEN"), "stop"),
    "stop_nullable_neutered": (_REAL.replace("AND NOT attisdropped AND attnotnull) THEN", "AND NOT attisdropped) THEN"), "stop"),
    "stop_missing_chart_neutered": (_REAL.replace("IF bad > 0 THEN", "IF false THEN"), "stop"),
    "owner_guard_neutered": (_REAL.replace("IF NOT pg_has_role(current_user, owner, 'USAGE') THEN", "IF false THEN"), "stop"),
    "existing_link_check_neutered": (_REAL.replace("IF cdef IS NOT NULL AND cdef IS DISTINCT FROM expected AND NOT (tbl = ANY (relink) AND cdef = relink_old) THEN", "IF false THEN"), "redef"),
    "active_runs_guard_neutered": (_REAL.replace("IF n_active > 0 THEN", "IF false THEN"), "runs"),
    "lock_timeout_removed": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "", 1), "lock"),
    "lock_timeout_session_wide": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';", 1), "lock"),
    "extra_change_caught_by_post_check": (_REAL.replace(_MUT_ANCHOR, "    ALTER TABLE public.charts ADD CONSTRAINT x_extra FOREIGN KEY (id) REFERENCES public.charts(id);\n" + _MUT_ANCHOR), "scenario"),
}


def test_mutants_are_real_mutations_of_the_real_file():
    for name, (sql, _) in _MUTANTS.items():
        assert sql != _REAL, f"mutant {name} did not change the file (the mutation pattern is stale)"


def test_the_real_file_produces_no_violations(db):
    assert _scenario(db, _REAL) == []
    assert _stop_scenario(db, _REAL) == []
    assert _redef_scenario(db, _REAL) == []
    assert _runs_scenario(db, _REAL) == []
    assert _lock_scenario(db, _REAL) == []


@pytest.mark.parametrize("name", sorted(_MUTANTS))
def test_every_mutant_is_caught(db, name):
    sql, kind = _MUTANTS[name]
    v = {"scenario": _scenario, "stop": _stop_scenario, "redef": _redef_scenario, "runs": _runs_scenario, "lock": _lock_scenario}[kind](db, sql)
    assert v, f"mutant {name} was NOT caught"
