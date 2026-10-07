"""Migration 1333 (Suvarna FIX1): make `ga_fact_identity` a REAL registered build asset.

  (1) asset_registry.ga_fact_identity: has_writer false -> true, depends_on '{}' -> the 11 ga_* assets that write chart_facts;
  (2) asset_registry.bo_pratijna: depends_on += 'ga_fact_identity';
  (3) GRANT INSERT, DELETE ON chart_fact_identity TO data_plane_builder (SELECT is 1262's).

LIVE test on a DISPOSABLE PostgreSQL cluster (initdb in a temp dir, unix socket only, torn down at the end), once per available major
version (15 = production, 17). The cluster/role layout, chart_facts / chart_fact_identity / asset_registry / build_runs DDL and the ACLs
are the ones of tests/test_migration_1262_chart_fact_identity_registration.py (read from the production catalog), with two differences that
matter for THIS migration:
  * the receipt-invalidation trigger function is the REAL one (production body, read-only 2026-10-08: UPDATE asset_freshness SET
    freshness_state='stale', reasons += 'registry_changed' WHERE asset_id = NEW.asset_id), not 1262's raising stub, because 1333 DOES
    update trigger columns on two rows and the test must observe exactly which freshness rows go stale;
  * the registry carries the 1262 post-state of ga_fact_identity (has_writer false, depends_on empty) and the builder already holds
    SELECT on the index (1262 applied).
The migration is applied AS amjis_app in ONE transaction (BEGIN; sql; COMMIT), like platform/scripts/migrate.ts.

Each scenario returns a list of VIOLATIONS; the real file must produce none. What they prove:
  apply_once   edges + has_writer land; bo_pratijna gains the edge appended last; english_description rewritten; the builder holds
               SELECT, INSERT, DELETE and none of UPDATE / TRUNCATE / REFERENCES / TRIGGER; the relacl diff over ALL relations is exactly
               the builder's new INSERT+DELETE on chart_fact_identity; the FK ON DELETE CASCADE is untouched; every other registry row is
               byte-identical; the trigger staled EXACTLY ga_fact_identity's and bo_pratijna's freshness rows (the bystanders stay fresh);
               count_sql / integrity_check_sql / scope / target_floor ... are unchanged; lock_timeout does not leak past COMMIT.
  idempotent   a second apply writes nothing (xmin of both rows, freshness rows, ACL unchanged) and reports the grants no-op.
  builder_e2e  before: the builder cannot DELETE/INSERT on the index; after: it can (delete-then-insert), and a chart_facts delete by the
               builder still cascades into the index (the FK is kept, by design).
  guards       active build run (planned/running/paused) refuses, completed does not; an upstream asset missing / inactive / without a
               writer refuses; a divergent ga_fact_identity shape refuses (rolled back whole, no grant); a missing ga_fact_identity row
               refuses; an inactive bo_pratijna refuses; an absent bo_pratijna is a NOTICE (seed carries the edge) and the rest applies;
               a non-owner executor refuses with the owner message BEFORE any write; a dependency cycle refuses.
Mutation tests rewrite the real SQL (grant removed / to PUBLIC / ALL / UPDATE added, guards and post-checks and read-back neutered, an
extra trigger column touched, ...) and require EVERY mutant to produce at least one violation.

HONEST LIMITS: this proves the migration's SQL on stock PostgreSQL with the production-shaped role structure; it does not read production.
`REQUIRE_PG_BINARIES=1` turns a missing binary from a skip into a failure.
"""
from __future__ import annotations

import re
from pathlib import Path

import psycopg
import pytest
from psycopg import errors as pgerr

from tests import test_migration_1262_chart_fact_identity_registration as m
from tests.test_migration_1262_chart_fact_identity_registration import cluster  # noqa: F401  (module-scoped disposable-cluster fixture)

_REPO = Path(__file__).resolve().parents[3]
MIGRATION = _REPO / "platform" / "migrations" / "1333_ga_fact_identity_writer_registration.sql"
REAL_SQL = MIGRATION.read_text(encoding="utf-8")

ASSET = "ga_fact_identity"
CONSUMER = "bo_pratijna"
UPSTREAM = sorted([
    "ga_ayurdaya", "ga_condition", "ga_dashas", "ga_nakshatra", "ga_panchanga", "ga_positions",
    "ga_sade_sati", "ga_sensitive", "ga_sensitive_degree", "ga_strength", "ga_structural",
])
BYSTANDERS = ["ga_vargas", "ga_yoga", "bo_laksana", "bo_sangati"]  # present and fresh; the migration must not stale them
CONSUMER_BEFORE = ["bo_laksana", "bo_sangati", "ga_vargas"]  # production, read-only 2026-10-08
BUILDER = "data_plane_builder"
VERSIONS = m.VERSIONS

REAL_TRIGGER_FN = """
CREATE FUNCTION public.nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE public.asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END $$
"""
STUB_FN_RE = re.compile(r"CREATE FUNCTION public\.nirmana_invalidate_registry_receipts\(\).*?END \$\$;", re.S)
REGISTRY_DDL = STUB_FN_RE.sub(REAL_TRIGGER_FN.strip() + ";", m.ASSET_REGISTRY_DDL)
FRESHNESS_DDL = """
CREATE TABLE public.asset_freshness (
  asset_id text NOT NULL, chart_id uuid NOT NULL, freshness_state text NOT NULL, reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
  observed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (asset_id, chart_id));
ALTER TABLE public.asset_freshness OWNER TO amjis_app
"""
COUNT_SQL = "SELECT count(*) FROM chart_fact_identity WHERE chart_id = $1"
INTEGRITY_SQL = "SELECT EXISTS (SELECT 1 FROM public.chart_fact_identity) AS integrity_passed"
OLD_DESCRIPTION = "Derived index ... NOT a built asset: it has no @register()'d writer (has_writer = false); hand-run G-IDX."


class Env1333(m.Env):
    """A fresh production-shaped database in the 1262 post-state, with the DAG neighbourhood of this migration."""

    def __init__(self, cl: m.Cluster, *, with_consumer: bool = True, with_ga_fact_identity_freshness: bool = True):
        self.cl = cl
        cl._n += 1
        self.db = f"u{cl._n}"
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} OWNER amjis_app TEMPLATE template0")
        with cl.connect(self.db, "postgres", autocommit=True) as c:
            for ddl in (m.CHART_FACTS_DDL, m.IDENTITY_DDL, REGISTRY_DDL, m.BUILD_RUNS_DDL, FRESHNESS_DDL):
                c.execute(ddl)
            for chart, build, n_ident in ((m.CHART_A, m.BUILD_A, 4), (m.CHART_B, m.BUILD_B, 3)):
                for i in range(6):
                    c.execute(
                        "INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key,"
                        " citation_ref, citation_human, source_calculation, verification_pass_status, engine_version, computed_at)"
                        " VALUES (%s,%s,'lahiri',%s,'graha_position',%s,'house_d1','c','c','s','two_pass_verified','e',now())",
                        (m._fact_id(chart, i), chart, build, ("SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS")[i]))
                    if i < n_ident:
                        c.execute(
                            "INSERT INTO public.chart_fact_identity (fact_id, chart_id, entity_kind, graha_code, parse_rule, parsed_from, build_id)"
                            " VALUES (%s,%s,'graha','SUN','bare_graha_subject','x',%s)", (m._fact_id(chart, i), chart, build))
            rows = [(a, "ganita", True, []) for a in UPSTREAM + ["ga_yoga", "ga_vargas"]]
            rows += [("bo_laksana", "bodha", True, []), ("bo_sangati", "bodha", True, [])]
            if with_consumer:
                rows.append((CONSUMER, "bodha", True, list(CONSUMER_BEFORE)))
            for aid, layer, writer, deps in rows:
                c.execute("INSERT INTO public.asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description,"
                          " storage_type, scope, has_writer, depends_on, catalog_status) VALUES (%s,%s,1,'x','x','x','postgres_table','per_chart',%s,%s,'CURRENT')",
                          (aid, layer, writer, deps))
            # the 1262 post-state of the asset itself
            c.execute("INSERT INTO public.asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type,"
                      " target_table, count_sql, target_floor, scope, is_active, asset_type, layer_name, layer_index, catalog_status, integrity_check_sql,"
                      " has_substeps, asset_kind, has_writer, domain, rung) VALUES (%s,'ganita',52,'x','Fact Identity Index',%s,'postgres_table',"
                      "'chart_fact_identity',%s,0,'per_chart',true,'data','Gaṇita','L1','CURRENT',%s,false,'data',false,'chart','R1')",
                      (ASSET, OLD_DESCRIPTION, COUNT_SQL, INTEGRITY_SQL))
            fresh = [a for a in UPSTREAM + BYSTANDERS + ([CONSUMER] if with_consumer else [])]
            if with_ga_fact_identity_freshness:
                fresh.append(ASSET)
            for a in fresh:
                c.execute("INSERT INTO public.asset_freshness (asset_id, chart_id, freshness_state) VALUES (%s,%s,'fresh')", (a, m.CHART_A))
            c.execute(m.ACL_SQL)
            c.execute("GRANT SELECT ON public.chart_fact_identity TO data_plane_builder")  # migration 1262 applied
            assert c.execute("SELECT has_table_privilege('data_plane_builder','public.chart_fact_identity','INSERT')").fetchone()[0] is False

    # ---- observation
    def reg(self, aid: str) -> dict | None:
        with self.admin() as c:
            cur = c.execute("SELECT *, xmin::text AS _xmin FROM public.asset_registry WHERE asset_id = %s", (aid,))
            row = cur.fetchone()
            return None if row is None else dict(zip([d.name for d in cur.description], row))

    def other_registry(self) -> list[str]:
        with self.admin() as c:
            return [r[0] for r in c.execute("SELECT t::text FROM public.asset_registry t WHERE asset_id NOT IN (%s,%s) ORDER BY asset_id", (ASSET, CONSUMER)).fetchall()]

    def freshness(self) -> dict[str, tuple[str, list]]:
        with self.admin() as c:
            return {r[0]: (r[1], r[2], r[3].isoformat()) for r in
                    c.execute("SELECT asset_id, freshness_state, reasons, observed_at FROM public.asset_freshness").fetchall()}

    def fk_delete_action(self) -> str:
        with self.admin() as c:
            return c.execute("SELECT confdeltype::text FROM pg_constraint WHERE conrelid='public.chart_fact_identity'::regclass AND contype='f'").fetchone()[0]


def _try(fn):
    try:
        fn()
        return None
    except Exception as exc:  # noqa: BLE001 - scenarios report any failure as data
        return exc


def _msg(exc) -> str:
    return "" if exc is None else str(exc).splitlines()[0]


def _stale_ids(before: dict, after: dict) -> set[str]:
    return {a for a in after if after[a][0] == "stale" and before[a][0] != "stale"}


# --------------------------------------------------------------------------------------------- scenarios

def sc_apply_once(cl, sql: str) -> list[str]:
    v: list[str] = []
    env = Env1333(cl)
    try:
        fresh0, acl0, other0 = env.freshness(), env.acls(), env.other_registry()
        before_asset, before_cons = env.reg(ASSET), env.reg(CONSUMER)
        notices: list[str] = []
        lock_after = env.apply(sql, notices=notices)
        if lock_after != "0":
            v.append(f"lock_timeout leaked past COMMIT: {lock_after}")
        a, c = env.reg(ASSET), env.reg(CONSUMER)
        if a["has_writer"] is not True:
            v.append("ga_fact_identity.has_writer is not true")
        if a["depends_on"] != UPSTREAM:
            v.append(f"ga_fact_identity.depends_on != the 11 sorted edges: {a['depends_on']}")
        if "migration 1333" not in a["english_description"] or "NOT a built asset" in a["english_description"]:
            v.append("english_description was not rewritten")
        for col in ("count_sql", "integrity_check_sql", "scope", "target_floor", "is_active", "target_table", "asset_kind", "asset_type", "sort_order",
                    "health_probe", "natural_key_partition", "has_substeps", "catalog_status", "layer", "writer_timeout_seconds"):
            if a[col] != before_asset[col]:
                v.append(f"ga_fact_identity.{col} changed: {before_asset[col]!r} -> {a[col]!r}")
        if c["depends_on"] != CONSUMER_BEFORE + [ASSET]:
            v.append(f"bo_pratijna.depends_on != before + [ga_fact_identity] (appended last): {c['depends_on']}")
        for col in c:
            if col not in ("depends_on", "_xmin") and c[col] != before_cons[col]:
                v.append(f"bo_pratijna.{col} changed")
        if env.other_registry() != other0:
            v.append("another registry row changed")
        fresh1 = env.freshness()
        staled = _stale_ids(fresh0, fresh1)
        if staled != {ASSET, CONSUMER}:
            v.append(f"staled set != {{ga_fact_identity, bo_pratijna}}: {sorted(staled)}")
        for a_id in BYSTANDERS + UPSTREAM:
            if fresh1[a_id] != fresh0[a_id]:
                v.append(f"bystander freshness row changed: {a_id}")
        if "registry_changed" not in fresh1[CONSUMER][1] or "registry_changed" not in fresh1[ASSET][1]:
            v.append("registry_changed reason missing on a staled row")
        p = env.privs(BUILDER)
        if not (p["SELECT"] and p["INSERT"] and p["DELETE"]):
            v.append(f"builder lacks a needed privilege: {p}")
        extra = [k for k in ("UPDATE", "TRUNCATE", "REFERENCES", "TRIGGER") if p[k]]
        if extra:
            v.append(f"builder holds more than SELECT/INSERT/DELETE: {extra}")
        acl1 = env.acls()
        changed = {k for k in set(acl0) | set(acl1) if acl0.get(k) != acl1.get(k)}
        if changed != {"chart_fact_identity"}:
            v.append(f"relacl changed on relations other than the index: {sorted(changed)}")
        else:
            added = set(acl1["chart_fact_identity"]) - set(acl0["chart_fact_identity"])
            if added != {"data_plane_builder=ard/amjis_app"} or set(acl0["chart_fact_identity"]) - set(acl1["chart_fact_identity"]) != {"data_plane_builder=r/amjis_app"}:
                v.append(f"relacl diff on the index is not exactly r -> ard for the builder: +{added}")
        for role in ("public", "role_web_serve", "role_jobs", "role_sidecar", "retrieval_census_ro", "suvarna_reader"):
            try:
                pp = env.privs(role) if role != "public" else None
            except Exception:  # noqa: BLE001
                continue
            if pp and (pp["INSERT"] or pp["DELETE"]) and role in ("role_web_serve", "role_jobs", "role_sidecar", "retrieval_census_ro", "suvarna_reader"):
                v.append(f"{role} gained a write privilege")
        if env.fk_delete_action() != "c":
            v.append("the FK ON DELETE CASCADE was altered")
        with env.admin() as adm:
            if adm.execute("SELECT count(*) FROM public.chart_fact_identity").fetchone()[0] != 7:
                v.append("index data rows changed")
    finally:
        env.drop()
    return v


def sc_idempotent(cl, sql: str) -> list[str]:
    v: list[str] = []
    env = Env1333(cl)
    try:
        env.apply(sql)
        a1, c1, acl1, f1 = env.reg(ASSET), env.reg(CONSUMER), env.acls(), env.freshness()
        notices: list[str] = []
        env.apply(sql, notices=notices)
        a2, c2 = env.reg(ASSET), env.reg(CONSUMER)
        if a2["_xmin"] != a1["_xmin"] or c2["_xmin"] != c1["_xmin"]:
            v.append("a second apply rewrote a registry row")
        if env.acls() != acl1:
            v.append("a second apply changed the ACLs")
        if env.freshness() != f1:
            v.append("a second apply moved a freshness row")
        if c2["depends_on"].count(ASSET) != 1:
            v.append("the consumer edge was duplicated")
        if not any("already holds INSERT" in n for n in notices) or not any("already holds DELETE" in n for n in notices):
            v.append("the second apply did not report the grants as no-ops")
    finally:
        env.drop()
    return v


def sc_builder_e2e(cl, sql: str) -> list[str]:
    v: list[str] = []
    env = Env1333(cl)
    try:
        victim = m._fact_id(m.CHART_A, 5)  # a chart_facts row with no identity row yet
        for stmt, params in (("DELETE FROM public.chart_fact_identity WHERE chart_id = %s", (m.CHART_A,)),
                             ("INSERT INTO public.chart_fact_identity (fact_id, chart_id, entity_kind, parse_rule, parsed_from) VALUES (%s,%s,'graha','r','p')", (victim, m.CHART_A))):
            conn = env.as_(BUILDER)
            try:
                exc = _try(lambda: conn.execute(stmt, params))
            finally:
                conn.rollback()
                conn.close()
            if not isinstance(exc, pgerr.InsufficientPrivilege):
                v.append(f"before: the builder was not refused ({_msg(exc)}): {stmt[:40]}")
        env.apply(sql)
        conn = env.as_(BUILDER)
        try:
            conn.execute("DELETE FROM public.chart_fact_identity WHERE chart_id = %s", (m.CHART_A,))
            conn.execute("INSERT INTO public.chart_fact_identity (fact_id, chart_id, entity_kind, parse_rule, parsed_from) VALUES (%s,%s,'graha','r','p')", (victim, m.CHART_A))
            n = conn.execute("SELECT count(*) FROM public.chart_fact_identity WHERE chart_id = %s", (m.CHART_A,)).fetchone()[0]
            if n != 1:
                v.append(f"after: delete-then-insert as the builder left {n} rows, expected 1")
            conn.execute("DELETE FROM public.chart_facts WHERE chart_id = %s", (m.CHART_A,))  # the builder owns chart_facts writes
            n = conn.execute("SELECT count(*) FROM public.chart_fact_identity WHERE chart_id = %s", (m.CHART_A,)).fetchone()[0]
            if n != 0:
                v.append("a chart_facts delete by the builder no longer cascades into the index (FK semantics changed)")
            exc = _try(lambda: conn.execute("UPDATE public.chart_fact_identity SET entity_kind = 'x'"))
            if not isinstance(exc, pgerr.InsufficientPrivilege):
                v.append("the builder can UPDATE the index")
            conn.rollback()
        finally:
            conn.close()
    except Exception as exc:  # noqa: BLE001
        v.append(f"unexpected: {exc!r}")
    finally:
        env.drop()
    return v


def _expect_refusal(env: Env1333, sql: str, needle: str, label: str, v: list[str], *, role: str = "amjis_app") -> None:
    pre_acl, pre_a, pre_c = env.acls(), env.reg(ASSET), env.reg(CONSUMER)
    exc = _try(lambda: env.apply(sql, role=role))
    if exc is None or needle not in str(exc):
        v.append(f"{label}: expected refusal containing {needle!r}, got {_msg(exc)!r}")
        return
    if env.acls() != pre_acl:
        v.append(f"{label}: a grant leaked past the refusal")
    a, c = env.reg(ASSET), env.reg(CONSUMER)
    if a is not None and (a["_xmin"] != pre_a["_xmin"] or a["has_writer"] != pre_a["has_writer"]):
        v.append(f"{label}: the asset row changed despite the refusal")
    if c is not None and pre_c is not None and c["depends_on"] != pre_c["depends_on"]:
        v.append(f"{label}: the consumer row changed despite the refusal")


def sc_guards(cl, sql: str) -> list[str]:
    v: list[str] = []
    # active builds
    for state in ("planned", "running", "paused"):
        env = Env1333(cl)
        try:
            env.run_sql("INSERT INTO public.build_runs (state) VALUES (%s)", (state,))
            _expect_refusal(env, sql, "build run(s) are active", f"active build {state}", v)
        finally:
            env.drop()
    env = Env1333(cl)
    try:
        env.run_sql("INSERT INTO public.build_runs (state) VALUES ('completed'), ('failed'), ('stopped')")
        if (exc := _try(lambda: env.apply(sql))) is not None:
            v.append(f"finished builds must not block: {_msg(exc)}")
    finally:
        env.drop()
    # upstream problems
    for label, stmt, needle in (
        ("upstream missing", f"DELETE FROM public.asset_registry WHERE asset_id = 'ga_strength'", "upstream asset(s) missing"),
        ("upstream inactive", f"UPDATE public.asset_registry SET is_active = false WHERE asset_id = 'ga_dashas'", "upstream asset(s) missing"),
        ("upstream without writer", f"UPDATE public.asset_registry SET has_writer = false WHERE asset_id = 'ga_sensitive_degree'", "upstream asset(s) missing"),
        ("upstream global scope", f"UPDATE public.asset_registry SET scope = 'global' WHERE asset_id = 'ga_nakshatra'", "upstream asset(s) missing"),
        ("asset row missing", f"DELETE FROM public.asset_registry WHERE asset_id = '{ASSET}'", "does not exist"),
        ("divergent shape: writer true, wrong deps", f"UPDATE public.asset_registry SET has_writer = true, depends_on = ARRAY['ga_positions'] WHERE asset_id = '{ASSET}'", "neither the 1262 shape"),
        ("divergent shape: writer false, deps present", f"UPDATE public.asset_registry SET depends_on = ARRAY['ga_positions'] WHERE asset_id = '{ASSET}'", "neither the 1262 shape"),
        ("consumer inactive", f"UPDATE public.asset_registry SET is_active = false WHERE asset_id = '{CONSUMER}'", "not an active per_chart asset"),
        ("cycle", "UPDATE public.asset_registry SET depends_on = ARRAY['bo_pratijna'] WHERE asset_id = 'ga_positions'", "dependency cycle"),
        ("divergent count_sql is never silently accepted", f"UPDATE public.asset_registry SET count_sql = 'SELECT 1' WHERE asset_id = '{ASSET}'", "does not read back"),
        ("builder already holds UPDATE", "GRANT UPDATE ON public.chart_fact_identity TO data_plane_builder", "holds more than SELECT, INSERT, DELETE"),
    ):
        env = Env1333(cl)
        try:
            env.run_sql(stmt)
            _expect_refusal(env, sql, needle, label, v)
        finally:
            env.drop()
    # absent consumer is a NOTICE, the rest applies
    env = Env1333(cl, with_consumer=False)
    try:
        notices: list[str] = []
        if (exc := _try(lambda: env.apply(sql, notices=notices))) is not None:
            v.append(f"absent bo_pratijna must not block: {_msg(exc)}")
        elif not any("is not in asset_registry" in n for n in notices) or env.reg(ASSET)["has_writer"] is not True or not env.privs(BUILDER)["INSERT"]:
            v.append("absent bo_pratijna: no NOTICE, or the rest of the migration did not apply")
    finally:
        env.drop()
    # non-owner executor refuses with the owner message before any write (outsider cannot act as amjis_app)
    env = Env1333(cl)
    try:
        env.run_sql("GRANT SELECT, UPDATE ON public.asset_registry TO outsider")
        env.run_sql("GRANT SELECT ON public.chart_fact_identity TO outsider")
        _expect_refusal(env, sql, "cannot act as the owner", "non-owner executor", v, role="outsider")
    finally:
        env.drop()
    return v


SCENARIOS = {
    "apply_once": sc_apply_once,
    "idempotent": sc_idempotent,
    "builder_e2e": sc_builder_e2e,
    "guards": sc_guards,
}


@pytest.mark.parametrize("scenario", sorted(SCENARIOS))
def test_real_migration_has_no_violations(cluster, scenario):
    violations = SCENARIOS[scenario](cluster, REAL_SQL)
    assert violations == [], f"{scenario}: " + "; ".join(violations)


def test_post_check_catches_a_warn_only_grant(cluster):
    """A GRANT issued by a role without grant option is only a WARNING in PostgreSQL; with the owner guard removed the post-check must still fail."""
    env = Env1333(cluster)
    try:
        env.run_sql("GRANT SELECT, UPDATE ON public.asset_registry TO registry_writer")
        env.run_sql("GRANT SELECT, UPDATE ON public.asset_freshness TO registry_writer")  # the receipt trigger updates it
        no_guard = re.sub(r"IF NOT pg_has_role\(current_user, owner_oid, 'USAGE'\) THEN.*?END IF;", "", REAL_SQL, count=1, flags=re.S)
        assert no_guard != REAL_SQL
        exc = _try(lambda: env.apply(no_guard, role="registry_writer"))
        assert exc is not None and "lacks INSERT" in str(exc), _msg(exc)
        assert not env.privs(BUILDER)["INSERT"]
    finally:
        env.drop()


# --------------------------------------------------------------------------------------------- static contract

def _code(sql: str) -> str:
    return "\n".join(l for l in sql.splitlines() if not l.lstrip().startswith("--"))


def static_violations(sql: str) -> list[str]:
    v: list[str] = []
    code = _code(sql)
    if not code.strip().startswith("SET LOCAL lock_timeout = '5s';"):
        v.append("lock_timeout must be the FIRST executable statement")
    if re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code):
        v.append("migrate.ts owns the transaction")
    if re.search(r"^\s*(DROP|TRUNCATE|REVOKE|ALTER|DELETE\s+FROM|INSERT\s+INTO)\b", code, re.I | re.M):
        v.append("a forbidden top-level statement")
    if re.search(r"\bPUBLIC\b", code):
        v.append("never PUBLIC")
    if "ALL TABLES" in code or "ALL PRIVILEGES" in code or "GRANT OPTION" in code:
        v.append("schema-wide / all-privileges / grant-option")
    if re.findall(r"GRANT\s+([^\n]*?)\s+ON\s", code) != ["%s"] or "ARRAY['INSERT', 'DELETE']" not in code:
        v.append("the one dynamic GRANT must take its privileges from the INSERT, DELETE loop")
    sets = re.findall(r"UPDATE public\.asset_registry\s+SET\s+(.*?)\s+WHERE", code, re.S)
    cols = sorted({c.strip().split("=")[0].strip() for st in sets for c in re.split(r",\n", st) if "=" in c})
    if cols != ["depends_on", "english_description", "has_writer"]:
        v.append(f"registry columns written: {cols}")
    return v


def test_static_contract():
    assert static_violations(REAL_SQL) == []
    for needle in ("STALING EFFECT", "nirmana_registry_receipt_invalidation", "bo_pratijna", "NEEDS A RE-RUN", "FK cascade", "DELIBERATELY KEPT",
                   "Trap 103", "ROLLBACK NOTE", "NOT RUN BY THIS MIGRATION", "asset_freshness", "ga_vargas (chart_divisionals)",
                   "no sequence"):
        assert needle in REAL_SQL, f"header no longer states: {needle}"


def test_upstream_set_is_exactly_the_chart_facts_writers():
    """The 11 edges are the ga_* writers whose code INSERTs/DELETEs chart_facts rows; computed here from source, not copied."""
    root = _REPO / "platform" / "python-sidecar"
    pat = re.compile(r"replace_prior_chart_facts\(|INSERT INTO (?:public\.)?chart_facts\b|DELETE FROM (?:public\.)?chart_facts\b|_insert_chart_facts\(")
    found = set()
    for adapter in sorted((root / "pipeline" / "orchestrator" / "writers").glob("ga_*.py")):
        asset = adapter.stem
        if asset == "ga_fact_identity":
            continue
        text = adapter.read_text(encoding="utf-8")
        files = [text]
        own = root / "ga_writers" / f"{asset}_writer.py"  # convention: ga_X -> ga_writers/ga_X_writer.py (ga_nakshatra keeps its logic in the adapter)
        if own.exists():
            files.append(own.read_text(encoding="utf-8"))
        # ga_structural also runs ga_daridra_postpass, which writes chart_facts through ga_structural's own delete-then-insert
        if any(pat.search(f) for f in files):
            found.add(asset)
    # ga_daridra_postpass is a helper of ga_structural; ga_structural's closure already includes it
    assert found == set(UPSTREAM), (sorted(found - set(UPSTREAM)), sorted(set(UPSTREAM) - found))
    sql_edges = re.search(r"v_deps\s+constant text\[\] := ARRAY\[(.*?)\];", REAL_SQL, re.S).group(1)
    assert sorted(re.findall(r"'(ga_\w+)'", sql_edges)) == UPSTREAM


# --------------------------------------------------------------------------------------------- mutation tests

def _once(old: str, new: str):
    def mut(sql: str) -> str:
        assert old in sql, f"mutation anchor not found: {old[:60]!r}"
        return sql.replace(old, new, 1)
    return mut


MUTANTS = {
    "grant_insert_removed": _once("ARRAY['INSERT', 'DELETE']", "ARRAY['DELETE']"),
    "grant_delete_removed": _once("ARRAY['INSERT', 'DELETE']", "ARRAY['INSERT']"),
    "grant_update_added": _once("ARRAY['INSERT', 'DELETE']", "ARRAY['INSERT', 'DELETE', 'UPDATE']"),
    "grant_truncate_added": _once("ARRAY['INSERT', 'DELETE']", "ARRAY['INSERT', 'DELETE', 'TRUNCATE']"),
    "grant_to_public": _once("TO data_plane_builder', p, rel);", "TO PUBLIC', p, rel);"),
    "active_build_guard_removed": _once("IF n_active <> 0 THEN", "IF false THEN"),
    "owner_guard_removed": lambda s: re.sub(r"IF NOT pg_has_role\(current_user, owner_oid, 'USAGE'\) THEN.*?END IF;", "", s, count=1, flags=re.S),
    "upstream_guard_removed": _once("IF missing IS NOT NULL THEN", "IF false THEN"),
    "shape_guard_removed": _once("IF NOT (\n        (cur_has_writer IS FALSE", "IF false AND NOT (\n        (cur_has_writer IS FALSE"),
    "cycle_check_removed": _once("IF cyc IS NOT NULL THEN", "IF false THEN"),
    "consumer_edge_dropped": _once("SET depends_on = COALESCE(depends_on, '{}'::text[]) || v_asset", "SET depends_on = COALESCE(depends_on, '{}'::text[])"),
    "edge_dropped": _once("'ga_sade_sati', 'ga_sensitive', 'ga_sensitive_degree'", "'ga_sade_sati', 'ga_sensitive'"),
    "has_writer_not_set": _once("SET has_writer          = true,", "SET has_writer          = has_writer,"),
    "description_not_rewritten": _once("english_description = v_description\n     WHERE asset_id = v_asset", "english_description = english_description\n     WHERE asset_id = v_asset"),
    "extra_trigger_column_touched": _once("english_description = v_description\n     WHERE asset_id = v_asset", "english_description = v_description, integrity_check_sql = 'SELECT true'\n     WHERE asset_id = v_asset"),
    "idempotency_where_removed": _once("AND v_asset <> ALL (COALESCE(depends_on, '{}'::text[]));", ";"),
    "postcheck_extra_priv_removed": _once("IF extra IS NOT NULL THEN", "IF false THEN"),
    "readback_neutered": _once("IF n_ok <> 1 THEN", "IF false THEN"),
    "lock_timeout_removed": _once("SET LOCAL lock_timeout = '5s';", ""),
    "all_registry_rows_staled": _once("WHERE asset_id = v_asset\n       AND (has_writer IS DISTINCT FROM true", "WHERE asset_id IS NOT NULL\n       AND (has_writer IS DISTINCT FROM true"),
}


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_mutant_is_killed(cluster, name):
    mutated = MUTANTS[name](REAL_SQL)
    assert mutated != REAL_SQL
    if static_violations(mutated):
        return
    for sc in SCENARIOS.values():
        try:
            if sc(cluster, mutated):
                return
        except Exception:  # noqa: BLE001 - a crash under a mutant is a kill
            return
    # the owner-guard mutant is additionally caught by the dedicated warn-only test
    if name == "owner_guard_removed":
        return
    pytest.fail(f"mutant {name} survived every scenario")
