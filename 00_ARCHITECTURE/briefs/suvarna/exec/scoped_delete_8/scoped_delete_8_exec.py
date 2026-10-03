#!/usr/bin/env python3
"""Gated ONE-SHOT executor: delete exactly the 8 `life_event_miss` phala_pramana rows of chart 1c826d5a (SS ruling N-109). DRAFT, HELD, NEVER RUN
against any real system by its author, NEVER APPLIED.

WHY. L4 step ph_pramana read the private, chart-scoped `life_events` WITHOUT a chart filter, so chart 1c826d5a (no life events of its own) holds 8
phala_pramana rows classified `life_event_miss` that can only have been derived from another chart's private events (PH_LIFEEVENTS_SCOPE_REPORT.md;
reader fix PR #3047). SS approved a one-shot, scoped delete of exactly those 8 DERIVED rows (computed rows: N-46 on people-entered data is untouched).

IRREVERSIBLE BY DESIGN. There is NO rollback leg and the rows are NOT copied (their jsonb could be derived from private text). The rows are regenerable:
rebuild ph_pramana for 1c826d5a after PR #3047.

WHAT IT DOES, in ONE transaction as the Cloud SQL administrator (`postgres`: CREATEROLE, not a superuser), COMMIT only if every check holds:
  s1  GRANT the administrator transient membership of suvarna_reader (SELECT-only reads) and data_plane_builder (the least-privileged role that can DELETE
      from phala_pramana: table ACL `ard`); only the memberships it lacked, revoked again in s5. The executor then MEASURES the pre-state itself (python,
      as suvarna_reader): counts and ids only, never a private column.
  s2  preconditions (SQL, raising): table shape, no FK/trigger/rule/view/inheritance, the logical referencers of a pramana id are exactly the known set and
      none refers to a bound id, no build in flight, EXACTLY 8 rows match (chart, life_event_miss), their ids equal the bound list, their non-private
      fingerprint equals the pinned one, none carries a life-event payload
  s3  as data_plane_builder: DELETE FROM ONLY phala_pramana WHERE chart_id = <bound> AND pramana_id = ANY(<the 8 bound ids>) AND evidence_type =
      'life_event_miss' RETURNING pramana_id; exactly 8 rows with exactly the bound ids, else RAISE
  s4  ASSERTING post-checks as suvarna_reader (RAISE, never WARN): the 8 ids gone, no (chart, marker) row left, the chart total is pre - 8, the OTHER charts'
      counts and id-set digest are unchanged, the surviving rows of the chart are exactly the pre-image minus the 8
  --  the executor re-measures the post-state itself (python) and applies its own commit conditions, independent of the SQL assertions
  s5  revoke the memberships granted in s1
MODES (every mode needs --expect-plan: the in-process administrator credential is fetched only for a plan hash the operator names)
  --count                          preconditions only (s1, s2 + python pre-measure), always ROLLBACK, nothing deleted
  --dry-run                        the whole transaction incl. the delete and every commit condition, prints the evidence digest, ROLLBACK
  --apply --expect-plan H --expect-evidence D
                                   same transaction; COMMIT only if every check holds and D equals this run's evidence digest

LAUNCH (GATE_V2). Never started directly: `exec/gate_v2/run_gated.sh <python3.11 absolute path> scoped_delete_8_exec.py <args>`. main() calls launch_gate() FIRST and
refuses (exit 93) without a verifying GATE_V2_LAUNCH marker. --apply refuses (exit 92, before any connection) under a different interpreter or driver than the
matching dry run (the runtime record is bound into the evidence digest as well). outcome.json is written in every mode and status (it also carries the
before/after counts, the deleted ids and the non-private fingerprint); a MISSING outcome.json means check the database. The administrator password is fetched
from Secret Manager inside this process ONLY after the plan hash matched, never printed or saved; tests inject a disposable connection and never reach
connect_admin(). The source runs on Python 3.11 and 3.12+. No row content is ever printed, logged or saved: counts, ids and hashes of NON-private columns only.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import signal
import subprocess
import sys
import tempfile

import psycopg

HERE = pathlib.Path(__file__).resolve().parent


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


PROJECT = "madhav-astrology"
LOCK_TIMEOUT = "5s"
STATEMENT_TIMEOUT = "120s"
SQL_FORWARD = HERE / "sd8_delete_life_event_miss_phala_pramana.sql"
EVIDENCE_ROOT = "/Users/Dev/suvarna-evidence/ScopedDelete8"

# ------------------------------------------------------------------------------------------------------------- the bound target
EXPECTED_DATABASE = "amjis"
EXPECTED_ADMIN = "postgres"              # the Cloud SQL administrator; the identity this plan names
SERVER_MAJOR = 15                        # production is 15.18; any other major fails closed
SCHEMA, TABLE = "public", "phala_pramana"
MARKER = "life_event_miss"
CHART = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
IDS = ("649c5828-ba9c-4ca8-9a7f-6ace81fad2e3", "767b84b4-4090-4383-a9a9-ada59a509b1d", "a3c855bb-9698-4c43-bb6b-c85ad1ec0a84",
       "adcfd0d2-e748-4741-9df5-619ad1e8d271", "c4fd0d7c-7502-4b63-bb61-8b693c38375b", "ccdf5abd-6339-48dc-adac-39d8877f2629",
       "db6cc6a0-91a5-4f2e-89ea-33c4fd23fc5c", "f44dea24-ada4-405d-bba7-fe094ce8e1e6")
# sha256 over the NON-private columns of the 8 rows (pramana_id, chart_id, anchor_id, evidence_type, evidence_strength_label, window_status, lel_entry_id IS NULL,
# lel_entry_jsonb IS NULL, epoch(computed_at)), '|'-joined per row, rows '\n'-joined in pramana_id order. Measured read-only on production 2026-10-03.
ROWS_FINGERPRINT = "bf270a4b5b3612827e5ea85885538a99ca4147fd62f1a86882c831c0ff21a4b6"
OWNER_ROLE = "amjis_app"
BUILDER = "data_plane_builder"
READER = "suvarna_reader"
ASSUMED = (READER, BUILDER)
# every column that can refer to a pramana id (catalog scan `~ 'pramana_ids?$'`); a new one fails closed
KNOWN_REFERENCERS = ("mimamsa_anchor_adjustment.derived_from_pramana_ids", "mimamsa_convergence_adjustment.derived_from_pramana_ids",
                     "mimamsa_fact_adjustment.derived_from_pramana_ids", "mimamsa_predictions.source_pramana_id",
                     "mimamsa_predictions__ssv_20260728b.source_pramana_id", "mimamsa_signal_adjustment.derived_from_pramana_ids",
                     "phala_pramana.pramana_id", "phala_pramana__ssv_20260728b.pramana_id")
STEP_FIRST, STEP_DELETE, STEP_LAST = "s1_assume_roles", "s3_delete_as_builder", "s5_restore_memberships"
COUNT_STEPS = ("s1_assume_roles", "s2_preconditions_as_reader")
RESTORE_NOTE = "irreversible; rows regenerable by rebuilding ph_pramana for 1c826d5a after PR #3047"

# ------------------------------------------------------------------------------------------------------ gate wiring (GATE_V2)
GATE_TBD = "TBD_BIND_AT_GATE_REVISION_3"        # the marker for an UNBOUND pin: launch_gate refuses while any pin is this value
# The three pins are the sha256 of exec/gate_v2 on origin/main (GATE_V2 revision 3, PR #2938), recomputed with shasum -a 256 when this package was written.
GATE_PINS = {"prerun_gate.py": "01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e",
             "run_gated.sh": "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076",
             "executor_standards.py": "bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135"}
GATE_DIR_ENV = "SD8_TEST_GATE_DIR"
TEST_EVIDENCE_ENV = "SD8_TEST_EVIDENCE_ROOT"
PYTEST_ENV = "PYTEST_CURRENT_TEST"
EXIT_NO_LAUNCH = 93
EXIT_TEST_ENV = 95
EXIT_INTERPRETER = 92        # --apply under a different interpreter (or driver) than the dry run, or no comparable record (free: the gate uses 1, 2, 64, 93-98, 128+n)
MODES = ("count", "dry-run", "apply")


def gate_dir(environ=None) -> pathlib.Path:
    """exec/gate_v2 next to this folder. SD8_TEST_GATE_DIR (tests only) is REFUSED, exit 95, outside a pytest run."""
    environ = os.environ if environ is None else environ
    if GATE_DIR_ENV in environ:
        if PYTEST_ENV not in environ:
            sys.stderr.write(f"REFUSED: {GATE_DIR_ENV} is set outside a pytest run; it would redirect the gate files.\n")
            raise SystemExit(EXIT_TEST_ENV)
        return pathlib.Path(environ[GATE_DIR_ENV])
    return HERE.parent / "gate_v2"


_STD: dict = {}


def standards(environ=None):
    d = gate_dir(environ)
    if str(d) not in _STD:
        _STD[str(d)] = _load("executor_standards_sd8_" + str(len(_STD)), d / "executor_standards.py")
    return _STD[str(d)]


def launch_gate(environ=None):
    """FIRST thing main() does. Refuses (exit 93) unless the gate pins are bound AND executor_standards.py equals its pin AND a verifying
    GATE_V2_LAUNCH marker (set by run_gated.sh after a passing gate; shas equal the live gate files and the pins) is present."""
    environ = os.environ if environ is None else environ
    try:
        es = standards(environ)
    except FileNotFoundError:
        sys.stderr.write(f"REFUSED: the GATE_V2 files are not at {gate_dir(environ)} (exec/gate_v2, PR #2938): this executor cannot be launched.\n")
        raise SystemExit(EXIT_NO_LAUNCH)
    if any(v == GATE_TBD for v in GATE_PINS.values()):
        sys.stderr.write("REFUSED: the GATE_V2 pins in this executor are TBD: the plan hash is PROVISIONAL and this executor cannot run.\n")
        raise SystemExit(EXIT_NO_LAUNCH)
    if es.sha256_file(es.__file__) != GATE_PINS["executor_standards.py"]:
        sys.stderr.write("REFUSED: executor_standards.py differs from the version pinned in this executor (GATE_PINS)\n")
        raise SystemExit(EXIT_NO_LAUNCH)
    return es.require_gate_launch(environ, gate_dir=str(gate_dir(environ)), expected_gate_sha=GATE_PINS["prerun_gate.py"],
                                  expected_launcher_sha=GATE_PINS["run_gated.sh"])


# ------------------------------------------------------------------------------------------------------------- plan text + hash
def sha_file(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def exec_sha(path=None) -> str:
    return sha_file(path or __file__)


# ---------------------------------------------------------------------------------------------------------------------- SQL leg
@dataclasses.dataclass(frozen=True)
class Leg:
    name: str
    sql_path: pathlib.Path
    assumed: tuple

    def text(self) -> str:
        return self.sql_path.read_bytes().decode("utf-8")

    @property
    def steps(self) -> tuple:
        return parse_steps(self.text())

    @property
    def sql_sha256(self) -> str:
        return hashlib.sha256(self.text().encode("utf-8")).hexdigest()


def parse_steps(text: str) -> tuple:
    """((step_name, sql), ...) from `-- @@STEP <name>` marker lines; the text before the first marker is the header and is never executed."""
    parts = re.split(r"(?m)^-- @@STEP (\w+)[ \t]*$", text)
    steps = tuple((parts[i], parts[i + 1].strip("\n") + "\n") for i in range(1, len(parts), 2))
    names = [n for n, _ in steps]
    if not steps or len(set(names)) != len(names):
        raise ValueError("the SQL file must hold at least one uniquely named `-- @@STEP` group")
    for _, sql in steps:
        if re.search(r"(?im)^[ \t]*(BEGIN|COMMIT|ROLLBACK|START[ \t]+TRANSACTION|ABORT)([ \t]+(WORK|TRANSACTION))?[ \t]*;", sql):
            raise ValueError("a step must not control the transaction: the executor owns it")
    return steps


def forward_leg() -> Leg:
    return Leg("forward", SQL_FORWARD, ASSUMED)


def sql_bound_values(text: str) -> dict:
    """The chart, id list and fingerprint literals bound in the SQL file (s1), read back so the executor can refuse a SQL edit that no longer equals its own."""
    def lit(name):
        m = re.search(r"set_config\('madhav\.sd8_" + name + r"', '([^']*)'", text)
        return None if m is None else m.group(1)
    return {"chart": lit("chart"), "ids": lit("ids"), "fp": lit("fp")}


# commit conditions the EXECUTOR measures itself (independently of the asserting SQL in the steps)
CHECKS = (
    "pre_server_major_is_15", "pre_database_is_expected", "pre_session_user_is_the_expected_administrator", "pre_roles_exist",
    "pre_admin_can_assume_the_roles", "pre_sql_bound_values_equal_the_executor_bound_values",
    "pre_table_is_an_ordinary_table_owned_by_amjis_app_without_rls", "pre_delete_role_can_delete_and_reader_cannot_write",
    "pre_no_foreign_key_references_the_table", "pre_no_user_trigger_rule_view_or_inheritance_on_the_table",
    "m_pre_measured", "m_pre_referencer_columns_are_the_known_set", "m_pre_dependents_are_zero", "m_pre_no_build_in_flight",
    "m_pre_exactly_8_rows_match_chart_and_marker", "m_pre_matching_ids_equal_the_bound_ids", "m_pre_fingerprint_equals_the_pinned_one",
    "m_pre_no_matching_row_carries_a_life_event_payload",
    "step_*",
    "m_post_measured", "m_post_the_8_ids_are_gone", "m_post_no_chart_marker_row_left", "m_post_chart_total_reduced_by_exactly_8",
    "m_post_other_charts_counts_unchanged", "m_post_other_charts_id_set_unchanged", "m_post_chart_survivors_are_the_pre_image_minus_the_8",
    "m_post_deleted_ids_equal_the_bound_ids",
    "post_table_owner_acl_constraints_unchanged", "post_no_new_trigger_or_rule", "post_memberships_restored",
)


def render_plan(sha: str | None = None, pins: dict | None = None) -> str:
    pins = pins or GATE_PINS
    sha = sha or exec_sha()
    f = forward_leg()
    lines = [
        "PLAN scoped_delete_8 (SS ruling N-109): one-shot scoped DELETE of the 8 derived life_event_miss phala_pramana rows of chart 1c826d5a. IRREVERSIBLE; rows are NOT copied.",
        f"target: {SCHEMA}.{TABLE} WHERE chart_id = {CHART} AND evidence_type = '{MARKER}' AND pramana_id = ANY(the 8 ids below); DELETE FROM ONLY; nothing else is written",
        f"bound ids ({len(IDS)}): {', '.join(IDS)}",
        f"non-private rows fingerprint (sha256, pinned): {ROWS_FINGERPRINT}",
        f"server: PostgreSQL major {SERVER_MAJOR}, database {EXPECTED_DATABASE}, session user {EXPECTED_ADMIN} (CREATEROLE, not a superuser)",
        f"roles: reads as {READER} (SELECT only); the DELETE as {BUILDER} (table ACL ard: the least-privileged role that can DELETE); transient membership, revoked in the last step",
        f"transaction: ONE, as the Cloud SQL administrator; SET LOCAL lock_timeout = {LOCK_TIMEOUT}, statement_timeout = {STATEMENT_TIMEOUT}; COMMIT only if every check holds",
        f"commit conditions: {', '.join(CHECKS)}",
        f"known columns that can refer to a pramana id: {', '.join(KNOWN_REFERENCERS)}",
        f"restore: {RESTORE_NOTE}",
        f"-- sql: {SQL_FORWARD.name} sha256 {f.sql_sha256}",
    ]
    for n, s in f.steps:
        lines += [f"-- step {n}", s.rstrip("\n")]
    lines += [f"-- gate pin {k}: {v}" for k, v in sorted(pins.items())]
    lines.append(f"-- executor: scoped_delete_8_exec.py sha256 {sha}")
    return "\n".join(lines)


def plan_hash_unbound(sha: str | None = None, pins: dict | None = None) -> str:
    return hashlib.sha256((render_plan(sha, pins) + "\n").encode()).hexdigest()


def plan_hash(sha: str | None = None, pins: dict | None = None, environ=None) -> str:
    """The BOUND plan hash: the unbound hash with the two gate shas folded in (executor_standards.bind_gate_into_plan_hash)."""
    pins = pins or GATE_PINS
    return standards(environ).bind_gate_into_plan_hash(plan_hash_unbound(sha, pins),
                                                        {"gate_sha256": pins["prerun_gate.py"], "run_gated_sha256": pins["run_gated.sh"]})


# ------------------------------------------------------------------------------------------------------------------ db plumbing
def secret(name: str) -> str:
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest", "--secret", name, "--project", PROJECT],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("secret access failed")
    return r.stdout.rstrip("\r\n")


def connect_admin():
    return psycopg.connect(host="127.0.0.1", port=5433, dbname=EXPECTED_DATABASE, user=EXPECTED_ADMIN,
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable", connect_timeout=15)


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=lambda s: sorted(s) if isinstance(s, (set, frozenset)) else str(s))


def one(cur, sql: str, params=None):
    cur.execute(sql, params)
    row = cur.fetchone()
    return None if row is None else (row[0] if len(row) == 1 else tuple(row))


_REL = ("FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = %s")
ROLES_USED = (OWNER_ROLE, BUILDER, READER)
IDS_CSV = ",".join(IDS)


def snap(cur) -> dict:
    """The catalog facts the plan reasons about, read WITHOUT any role switch (pure pg_catalog queries: no USAGE on public is needed)."""
    d: dict = {}
    d["who"] = one(cur, "SELECT current_user::text, session_user::text, (SELECT rolsuper FROM pg_roles WHERE rolname = current_user), "
                        "(SELECT rolcreaterole FROM pg_roles WHERE rolname = current_user), current_setting('server_version_num')::int, current_database()::text")
    d["roles_exist"] = {r: bool(one(cur, "SELECT count(*) FROM pg_roles WHERE rolname = %s", (r,))) for r in ROLES_USED}
    d["role_is_super"] = {r: bool(one(cur, "SELECT COALESCE((SELECT rolsuper FROM pg_roles WHERE rolname = %s), false)", (r,))) for r in ROLES_USED}
    d["memberships"] = {r: bool(one(cur, "SELECT pg_has_role(current_user, %s, 'MEMBER')", (r,))) for r in ASSUMED if d["roles_exist"].get(r)}
    d["table"] = one(cur, "SELECT pg_get_userbyid(c.relowner)::text, c.relkind::text, c.relrowsecurity, c.relforcerowsecurity, COALESCE(c.relacl::text, 'NULL') " + _REL,
                     (SCHEMA, TABLE))
    # has_table_privilege(role, rel, 'A,B') is true if the role holds ANY of the listed privileges: SELECT and DELETE are therefore tested one by one
    d["privs"] = one(cur, "SELECT has_table_privilege(%s, c.oid, 'SELECT') AND has_table_privilege(%s, c.oid, 'DELETE'), has_table_privilege(%s, c.oid, 'UPDATE,TRUNCATE'), "
                          "has_table_privilege(%s, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE') " + _REL,
                     (BUILDER, BUILDER, BUILDER, READER, SCHEMA, TABLE)) if d["roles_exist"][BUILDER] and d["roles_exist"][READER] else None
    d["fk_referencing"] = one(cur, "SELECT count(*) FROM pg_constraint k JOIN pg_class c ON c.oid = k.confrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
                                   "WHERE n.nspname = %s AND c.relname = %s AND k.contype = 'f'", (SCHEMA, TABLE))
    # built from catalog columns, NOT pg_get_constraintdef: that text qualifies names by search_path visibility, which depends on the role's USAGE on public
    # (the administrator has none) and changed between two reads in one transaction on the mirror
    d["constraints_md5"] = one(cur, "SELECT md5(COALESCE(string_agg(concat_ws(':', k.conname, k.contype::text, COALESCE(k.conkey::text, ''), COALESCE(k.confkey::text, ''), "
                                    "k.confrelid::oid::text, k.confdeltype::text, k.confupdtype::text, k.convalidated::text, COALESCE(pg_get_expr(k.conbin, k.conrelid), '')), "
                                    "',' ORDER BY k.conname), '')) "
                                    "FROM pg_constraint k JOIN pg_class c ON c.oid = k.conrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
                                    "WHERE n.nspname = %s AND c.relname = %s", (SCHEMA, TABLE))
    d["user_triggers"] = one(cur, "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid JOIN pg_namespace n ON n.oid = c.relnamespace "
                                  "WHERE n.nspname = %s AND c.relname = %s AND NOT t.tgisinternal", (SCHEMA, TABLE))
    d["rules"] = one(cur, "SELECT count(*) FROM pg_rewrite r JOIN pg_class c ON c.oid = r.ev_class JOIN pg_namespace n ON n.oid = c.relnamespace "
                          "WHERE n.nspname = %s AND c.relname = %s AND r.rulename <> '_RETURN'", (SCHEMA, TABLE))
    d["dependent_views"] = one(cur, "SELECT count(*) FROM pg_depend d JOIN pg_rewrite r ON r.oid = d.objid AND d.classid = 'pg_rewrite'::regclass "
                                    "JOIN pg_class t ON t.oid = d.refobjid JOIN pg_namespace n ON n.oid = t.relnamespace "
                                    "WHERE n.nspname = %s AND t.relname = %s AND r.ev_class <> t.oid", (SCHEMA, TABLE))
    d["inheritance"] = one(cur, "SELECT count(*) FROM pg_inherits i JOIN pg_class c ON c.oid IN (i.inhparent, i.inhrelid) JOIN pg_namespace n ON n.oid = c.relnamespace "
                                "WHERE n.nspname = %s AND c.relname = %s", (SCHEMA, TABLE))
    return d


class Checks:
    def __init__(self) -> None:
        self.items: list[tuple[str, bool, str | None]] = []

    def chk(self, name: str, ok: bool, detail=None) -> bool:
        self.items.append((name, bool(ok), None if detail is None else str(detail)[:300]))
        return bool(ok)

    @property
    def failed(self) -> list[str]:
        return [n for n, ok, _ in self.items if not ok]


def pre_checks(leg: Leg, pre: dict, ck: Checks) -> None:
    who = pre["who"]       # (current_user, session_user, rolsuper, rolcreaterole, server_version_num, current_database)
    ck.chk("pre_server_major_is_15", who[4] // 10000 == SERVER_MAJOR, f"server_version_num={who[4]} expected major {SERVER_MAJOR}")
    ck.chk("pre_database_is_expected", who[5] == EXPECTED_DATABASE, f"database={who[5]} expected {EXPECTED_DATABASE}")
    ck.chk("pre_session_user_is_the_expected_administrator", who[0] == EXPECTED_ADMIN and who[1] == EXPECTED_ADMIN,
           f"current_user={who[0]} session_user={who[1]} expected {EXPECTED_ADMIN}")
    ck.chk("pre_roles_exist", all(pre["roles_exist"].get(r) for r in ROLES_USED), {r: pre["roles_exist"].get(r) for r in ROLES_USED})
    can = all(pre["memberships"].get(r) or (who[3] and not pre["role_is_super"].get(r) and pre["roles_exist"].get(r)) for r in leg.assumed) \
        and (who[4] < 160000 or bool(who[2]))
    ck.chk("pre_admin_can_assume_the_roles", can, f"admin={who[0]} super={who[2]} createrole={who[3]} server_version_num={who[4]}")
    bound = sql_bound_values(leg.text())
    ck.chk("pre_sql_bound_values_equal_the_executor_bound_values",
           bound == {"chart": CHART, "ids": IDS_CSV, "fp": ROWS_FINGERPRINT}, "the chart / id list / fingerprint literal in the SQL file differs from the executor's own")
    t = pre["table"]
    ck.chk("pre_table_is_an_ordinary_table_owned_by_amjis_app_without_rls",
           t is not None and t[0] == OWNER_ROLE and t[1] == "r" and t[2] is False and t[3] is False, None if t is None else (t[0], t[1], t[2], t[3]))
    p = pre["privs"]
    ck.chk("pre_delete_role_can_delete_and_reader_cannot_write", p is not None and p[0] is True and p[1] is False and p[2] is False, p)
    ck.chk("pre_no_foreign_key_references_the_table", pre["fk_referencing"] == 0, pre["fk_referencing"])
    ck.chk("pre_no_user_trigger_rule_view_or_inheritance_on_the_table",
           pre["user_triggers"] == 0 and pre["rules"] == 0 and pre["dependent_views"] == 0 and pre["inheritance"] == 0,
           {k: pre[k] for k in ("user_triggers", "rules", "dependent_views", "inheritance")})


# ---------------------------------------------------------------------------------------------------------- the executor's own measurement
DEPENDENT_QUERIES = {
    "mimamsa_predictions": "SELECT count(*) FROM public.mimamsa_predictions t WHERE t.source_pramana_id ~ %(rx)s OR t::text ~ %(rx)s",
    "mimamsa_predictions__ssv_20260728b": "SELECT count(*) FROM public.mimamsa_predictions__ssv_20260728b t WHERE t.source_pramana_id ~ %(rx)s OR t::text ~ %(rx)s",
    "mimamsa_anchor_adjustment": "SELECT count(*) FROM public.mimamsa_anchor_adjustment t WHERE t.derived_from_pramana_ids::text ~ %(rx)s",
    "mimamsa_convergence_adjustment": "SELECT count(*) FROM public.mimamsa_convergence_adjustment t WHERE t.derived_from_pramana_ids::text ~ %(rx)s",
    "mimamsa_fact_adjustment": "SELECT count(*) FROM public.mimamsa_fact_adjustment t WHERE t.derived_from_pramana_ids::text ~ %(rx)s",
    "mimamsa_signal_adjustment": "SELECT count(*) FROM public.mimamsa_signal_adjustment t WHERE t.derived_from_pramana_ids::text ~ %(rx)s",
    "phala_pramana__ssv_20260728b": "SELECT count(*) FROM public.phala_pramana__ssv_20260728b t WHERE t.pramana_id = ANY (string_to_array(%(ids)s, ',')::uuid[])",
}


def measure(cur, with_dependents: bool = True) -> dict:
    """Counts and ids only (never a private column), read as suvarna_reader (SELECT only). The caller holds the membership."""
    cur.execute("SET LOCAL ROLE " + READER)
    try:
        m: dict = {}
        p = {"chart": CHART, "ids": IDS_CSV, "marker": MARKER, "rx": "|".join(IDS)}
        cur.execute("SELECT chart_id::text, count(*) FROM public.phala_pramana GROUP BY 1 ORDER BY 1")
        by_chart = {k: int(v) for k, v in cur.fetchall()}
        m["by_chart"] = by_chart
        m["chart_total"] = by_chart.get(CHART, 0)
        m["other_by_chart"] = {k: v for k, v in by_chart.items() if k != CHART}
        cur.execute("SELECT count(*), COALESCE(array_agg(pramana_id::text ORDER BY pramana_id), '{}'::text[]), "
                    "count(*) FILTER (WHERE lel_entry_id IS NOT NULL OR lel_entry_jsonb IS NOT NULL), "
                    "encode(sha256(convert_to(string_agg(concat_ws('|', pramana_id::text, chart_id::text, anchor_id::text, evidence_type, evidence_strength_label, "
                    "window_status, (lel_entry_id IS NULL)::text, (lel_entry_jsonb IS NULL)::text, extract(epoch FROM computed_at)::text), E'\\n' "
                    "ORDER BY pramana_id), 'UTF8')), 'hex') FROM public.phala_pramana WHERE chart_id = %(chart)s::uuid AND evidence_type = %(marker)s", p)
        n, ids, payload, fp = cur.fetchone()
        m["match_n"], m["match_ids"], m["match_payload_n"], m["match_fingerprint"] = int(n), list(ids), int(payload), fp
        cur.execute("SELECT count(*) FROM public.phala_pramana WHERE pramana_id = ANY (string_to_array(%(ids)s, ',')::uuid[])", p)
        m["bound_ids_present_n"] = int(cur.fetchone()[0])
        cur.execute("SELECT encode(sha256(convert_to(COALESCE(string_agg(pramana_id::text, ',' ORDER BY pramana_id), ''), 'UTF8')), 'hex') "
                    "FROM public.phala_pramana WHERE chart_id <> %(chart)s::uuid", p)
        m["other_ids_digest"] = cur.fetchone()[0]
        cur.execute("SELECT encode(sha256(convert_to(COALESCE(string_agg(pramana_id::text, ',' ORDER BY pramana_id), ''), 'UTF8')), 'hex') "
                    "FROM public.phala_pramana WHERE chart_id = %(chart)s::uuid AND NOT (pramana_id = ANY (string_to_array(%(ids)s, ',')::uuid[]))", p)
        m["chart_rest_ids_digest"] = cur.fetchone()[0]
        cur.execute("SELECT count(*) FILTER (WHERE chart_id = %(chart)s::uuid), count(*) FROM public.build_runs WHERE state IN ('planned', 'running', 'paused')", p)
        m["builds_in_flight_on_chart"], m["builds_in_flight_any"] = (int(x) for x in cur.fetchone())
        cur.execute("SELECT COALESCE(string_agg(c.relname || '.' || a.attname, ',' ORDER BY c.relname COLLATE \"C\", a.attname COLLATE \"C\"), '') FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid "
                    "WHERE c.relnamespace = 'public'::regnamespace AND c.relkind IN ('r', 'p', 'v', 'm', 'f') AND a.attnum > 0 AND NOT a.attisdropped "
                    "AND a.attname ~ 'pramana_ids?$'")
        m["referencer_columns"] = cur.fetchone()[0]
        if with_dependents:
            m["dependents"] = {}
            for name, q in DEPENDENT_QUERIES.items():
                cur.execute(q, p)
                m["dependents"][name] = int(cur.fetchone()[0])
        return m
    finally:
        cur.execute("RESET ROLE")


def pre_measure_checks(m: dict, ck: Checks) -> None:
    ck.chk("m_pre_measured", True)
    ck.chk("m_pre_referencer_columns_are_the_known_set", m["referencer_columns"] == ",".join(sorted(KNOWN_REFERENCERS)), m["referencer_columns"])
    dep = m["dependents"]
    ck.chk("m_pre_dependents_are_zero", all(v == 0 for v in dep.values()) and set(dep) == set(DEPENDENT_QUERIES), {k: v for k, v in dep.items() if v})
    ck.chk("m_pre_no_build_in_flight", m["builds_in_flight_any"] == 0 and m["builds_in_flight_on_chart"] == 0,
           {"any": m["builds_in_flight_any"], "chart": m["builds_in_flight_on_chart"]})
    ck.chk("m_pre_exactly_8_rows_match_chart_and_marker", m["match_n"] == len(IDS) == 8, f"{m['match_n']} rows match (chart, {MARKER}), expected exactly 8")
    ck.chk("m_pre_matching_ids_equal_the_bound_ids", m["match_ids"] == sorted(IDS), f"matching ids: {m['match_ids']}")
    ck.chk("m_pre_fingerprint_equals_the_pinned_one", m["match_fingerprint"] == ROWS_FINGERPRINT, m["match_fingerprint"])
    ck.chk("m_pre_no_matching_row_carries_a_life_event_payload", m["match_payload_n"] == 0, f"{m['match_payload_n']} matching row(s) carry lel_entry_id/lel_entry_jsonb")


def post_measure_checks(pre_m: dict, m: dict, deleted: list, ck: Checks) -> None:
    ck.chk("m_post_measured", True)
    ck.chk("m_post_the_8_ids_are_gone", m["bound_ids_present_n"] == 0, f"{m['bound_ids_present_n']} of the bound ids still present")
    ck.chk("m_post_no_chart_marker_row_left", m["match_n"] == 0, f"{m['match_n']} (chart, {MARKER}) rows left")
    ck.chk("m_post_chart_total_reduced_by_exactly_8", m["chart_total"] == pre_m["chart_total"] - 8, f"{pre_m['chart_total']} -> {m['chart_total']}")
    ck.chk("m_post_other_charts_counts_unchanged", m["other_by_chart"] == pre_m["other_by_chart"], {"pre": pre_m["other_by_chart"], "post": m["other_by_chart"]})
    ck.chk("m_post_other_charts_id_set_unchanged", m["other_ids_digest"] == pre_m["other_ids_digest"])
    ck.chk("m_post_chart_survivors_are_the_pre_image_minus_the_8",
           m["chart_rest_ids_digest"] == pre_m["chart_rest_ids_digest"] and m["chart_total"] == pre_m["chart_total"] - 8)
    ck.chk("m_post_deleted_ids_equal_the_bound_ids", deleted == sorted(IDS), f"deleted ids: {deleted}")


def post_checks(pre: dict, post: dict, ck: Checks) -> None:
    ck.chk("post_table_owner_acl_constraints_unchanged", post["table"] == pre["table"] and post["constraints_md5"] == pre["constraints_md5"]
           and post["fk_referencing"] == pre["fk_referencing"], None if post["table"] == pre["table"] else "owner/ACL/rls differs from the pre-image")
    ck.chk("post_no_new_trigger_or_rule", post["user_triggers"] == pre["user_triggers"] and post["rules"] == pre["rules"])
    ck.chk("post_memberships_restored", post["memberships"] == pre["memberships"], {"pre": pre["memberships"], "post": post["memberships"]})


def read_deleted_ids(cur) -> list:
    cur.execute("SELECT current_setting('madhav.sd8_deleted_ids', true)")
    raw = cur.fetchone()[0]
    return sorted(raw.split(",")) if raw else []


def run_leg(conn, leg: Leg, mode: str, out) -> dict:
    """mode: count (s1, s2, python pre-measure; nothing deleted) | dry-run | apply. Returns the checks, the evidence digest and commit_ok; the CALLER commits or
    rolls back."""
    ck = Checks()
    cur = conn.cursor()
    cur.execute(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'")
    cur.execute(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'")
    pre = snap(cur)
    pre_checks(leg, pre, ck)
    post, pre_m, post_m, deleted = None, None, None, []
    full = mode != "count"
    complete = False
    if not ck.failed:
        steps = [s for s in leg.steps if full or s[0] in COUNT_STEPS]
        complete = True
        for name, sql in steps:
            if name == STEP_DELETE and ck.failed:
                complete = False
                break
            if name == STEP_LAST:
                if ck.failed:
                    complete = False
                    break
                try:
                    deleted = read_deleted_ids(cur)
                    post_m = measure(cur, with_dependents=False)
                except psycopg.Error as exc:
                    ck.chk("m_post_measured", False, f"{type(exc).__name__} {getattr(exc.diag, 'sqlstate', None)}")
                    complete = False
                    break
                post_measure_checks(pre_m, post_m, deleted, ck)
                if ck.failed:
                    complete = False
                    break
            out(f"step {name}")
            try:
                cur.execute(sql)
            except psycopg.Error as exc:
                ck.chk("step_" + name, False, f"{type(exc).__name__} {getattr(exc.diag, 'sqlstate', None)}: {getattr(exc.diag, 'message_primary', '')}")
                complete = False
                break
            ck.chk("step_" + name, True)
            if name == STEP_FIRST:
                try:
                    pre_m = measure(cur)
                except psycopg.Error as exc:
                    ck.chk("m_pre_measured", False, f"{type(exc).__name__} {getattr(exc.diag, 'sqlstate', None)}: {getattr(exc.diag, 'message_primary', '')}")
                    complete = False
                    break
                pre_measure_checks(pre_m, ck)       # recorded; s2 (the SQL preconditions) still runs, the DELETE step does not while anything has failed
        if complete and full and not ck.failed:
            post = snap(cur)
            post_checks(pre, post, ck)
    parts = {"leg": leg.name, "sql_sha256": leg.sql_sha256, "bound": {"chart": CHART, "ids": list(IDS), "fingerprint": ROWS_FINGERPRINT}, "pre": pre, "post": post,
             "pre_measure": pre_m, "post_measure": post_m, "deleted_ids": deleted, "checks": [[n, ok] for n, ok, _ in ck.items], "runtime": runtime_record()}
    digest = hashlib.sha256(canonical(parts).encode()).hexdigest()
    commit_ok = full and complete and post is not None and not ck.failed
    report = [f"leg {leg.name} mode {mode}"] + [f"  {'ok  ' if ok else 'FAIL'} {n}" + (f"  ({d})" if d and not ok else "") for n, ok, d in ck.items]
    extra = outcome_extra(pre_m, post_m, deleted)
    return {"checks": ck, "evidence_digest": digest, "commit_ok": commit_ok, "pre": pre, "post": post, "pre_measure": pre_m, "post_measure": post_m,
            "deleted_ids": deleted, "report": report, "digest_parts": parts, "outcome_extra": extra}


def outcome_extra(pre_m, post_m, deleted) -> dict:
    """Counts, ids and a hash of NON-private columns only; added to outcome.json (never any row content)."""
    return {"target": f"{SCHEMA}.{TABLE}", "bound_chart": CHART, "bound_ids": list(IDS), "marker": MARKER,
            "rows_deleted_in_transaction": len(deleted), "deleted_ids": list(deleted),
            "deleted_rows_nonprivate_fingerprint_sha256": (pre_m or {}).get("match_fingerprint"),
            "chart_total_before": (pre_m or {}).get("chart_total"), "chart_total_after": (post_m or {}).get("chart_total"),
            "other_charts_before": (pre_m or {}).get("other_by_chart"), "other_charts_after": (post_m or {}).get("other_by_chart"),
            "after_is_measured_inside_the_transaction": True, "transaction_committed": False, "irreversible": True, "restore": RESTORE_NOTE}


def write_evidence(run_dir: pathlib.Path, res: dict, result: dict) -> None:
    """Best effort after the transaction decision."""
    try:
        write_private(run_dir / "report.txt", "\n".join(res.get("report") or []) + "\n")
        write_private(run_dir / "digest_parts.json", canonical(res.get("digest_parts") or {}) + "\n")
        write_private(run_dir / "result.json", json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    except OSError:
        result.setdefault("warnings", []).append("evidence files could not be fully written")


# ------------------------------------------------------------------------------------------------------------------------- evidence
def resolve_evidence_root(flag=None, environ=None) -> str:
    environ = os.environ if environ is None else environ
    if TEST_EVIDENCE_ENV not in environ:
        return EVIDENCE_ROOT
    if PYTEST_ENV not in environ:
        sys.stderr.write(f"REFUSED: {TEST_EVIDENCE_ENV} is set outside a pytest run; it would redirect the evidence directory.\n")
        raise SystemExit(EXIT_TEST_ENV)
    root = flag or environ[TEST_EVIDENCE_ENV]
    if not root:
        sys.stderr.write(f"REFUSED: {TEST_EVIDENCE_ENV} is set but empty: refusing to fall back to the real evidence root.\n")
        raise SystemExit(EXIT_TEST_ENV)
    return root


class EvidenceError(Exception):
    pass


def mkdir_0700(path) -> None:
    path = pathlib.Path(path)
    missing = [p for p in [path] + list(path.parents) if not p.exists()]
    for p in reversed(missing):
        p.mkdir(mode=0o700)
        os.chmod(p, 0o700)
    if not missing:
        try:
            os.chmod(path, 0o700)
        except OSError:
            pass


def make_run_dir(root, mode: str, ts: str) -> pathlib.Path:
    try:
        rootp = pathlib.Path(root)
        mkdir_0700(rootp)
        d = rootp / f"{mode}_{ts}"
        d.mkdir(mode=0o700)            # NOT exist_ok: a collision aborts, never overwrites another run's evidence
        os.chmod(d, 0o700)
    except OSError as exc:
        raise EvidenceError(f"cannot create the evidence directory under {root} ({type(exc).__name__})")
    return d


def write_private(path: pathlib.Path, text: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(text)


# ------------------------------------------------------------------------------------------------------- outcome / execute
_SAFE_CLASS: dict = {}

RUNTIME_KEYS = ("python_executable", "python_version", "psycopg_version", "libpq_version")


def runtime_record() -> dict:
    """WHICH interpreter and driver is running: sys.executable, the full sys.version, psycopg.__version__ and the libpq version (an int, e.g. 170002). Recorded in
    outcome.json (every status) and in result.json, and BOUND INTO THE EVIDENCE DIGEST (run_leg): the dry run and the apply must use the SAME interpreter and
    driver, and the apply refuses by itself otherwise (interpreter_precheck, then the digest)."""
    return {"python_executable": sys.executable, "python_version": sys.version, "psycopg_version": psycopg.__version__,
            "libpq_version": psycopg.pq.version()}


def add_to_outcome(path, extra: dict):
    """Adds runtime_record() and the executor's own fields (counts / ids / fingerprint) to outcome.json, in every status. The gate's executor_standards.py is
    pinned byte-for-byte (GATE_PINS), so the fields are added here, atomically (temp file + os.replace in the same directory, mode 0600), right after the
    standard write."""
    with open(path) as f:
        body = json.load(f)
    body.update(runtime_record())
    body.update(extra)
    d = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(prefix=".outcome.", dir=d)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps(body, indent=2, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def safe_outcome_class(es):
    """executor_standards.outcome_guard whose own file write can never mask the real result, with a committed flag: after COMMIT an interruption records
    `applied` with a warning, never `failed`."""
    if id(es) in _SAFE_CLASS:
        return _SAFE_CLASS[id(es)]

    class SafeOutcome(es.outcome_guard):
        write_error = None
        interpreter_record_error = None        # the standard outcome.json exists but the extra record could not be added
        committed = False
        commit_unknown = None              # class name of the exception conn.commit() itself raised: the server MAY have committed
        commit_digest = None
        extra: dict = {}

        def mark_committed(self, digest):
            """Called IMMEDIATELY after conn.commit(): from here on the truth is `applied`, whatever happens next."""
            self.committed, self.commit_digest = True, digest
            self.extra = {**self.extra, "transaction_committed": True, "after_is_measured_inside_the_transaction": False}

        def mark_commit_unknown(self, digest, exc_name):
            """conn.commit() raised (e.g. the connection dropped at the acknowledgement): neither applied nor failed is known."""
            self.commit_unknown, self.commit_digest = exc_name, digest

        def _write(self, status, digest=None, checks=(), warnings=()):
            try:
                super()._write(status, digest, checks, warnings)
            except OSError as exc:
                self.write_error = type(exc).__name__
                self.done = True
                return
            try:
                add_to_outcome(self.path, self.extra)
            except Exception as exc:        # the standard file exists but lacks the extra record: reported as exactly that, never a crash after COMMIT
                self.interpreter_record_error = type(exc).__name__

        @staticmethod
        def _warn(text):
            """stderr is best effort: a closed / broken stderr (SIGHUP with the terminal gone) must never cost the outcome file."""
            try:
                sys.stderr.write(text)
                sys.stderr.flush()
            except BaseException:
                pass

        def __exit__(self, exc_type, exc, tb):
            if self.commit_unknown and not self.done:
                self._write("commit_state_unknown", self.commit_digest, (), ["commit_raised:" + self.commit_unknown])
                self._warn("WARNING: COMMIT STATE UNKNOWN (%s raised by commit()): the delete may or may not be committed. outcome.json records "
                           "commit_state_unknown. CHECK THE DATABASE before doing anything else.\n" % self.commit_unknown)
                return False
            if self.committed and not self.done:
                why = re.sub(r"[^A-Za-z0-9_.:\-]", "_", exc_type.__name__ if exc_type is not None else "outcome_not_declared")[:40]
                self._write("applied", self.commit_digest, (), ["outcome_write_failed_after_commit:" + why])      # the outcome FIRST
                self._warn("WARNING: THE COMMIT HAPPENED but the run was interrupted (%s) before outcome.json was recorded; recorded "
                           "applied with a warning. Verify in the database.\n" % why)
                return False
            return super().__exit__(exc_type, exc, tb)

    _SAFE_CLASS[id(es)] = SafeOutcome
    return SafeOutcome


def conclude(o, result, kind, digest=None, checks=()):
    if kind == "dry_run":
        o.dry_run(digest)
    elif kind == "applied":
        o.applied(digest)
    else:
        o.fail(list(checks) or ["refused_unspecified"], digest)
    if o.write_error:
        result.setdefault("warnings", []).append(
            "outcome.json could not be written (%s)%s" % (o.write_error, "; THE COMMIT HAPPENED" if kind == "applied" else ""))
    else:
        result["outcome_file"] = o.path
        if o.interpreter_record_error:
            result.setdefault("warnings", []).append(
                "outcome.json written without the extra record (%s)%s" % (o.interpreter_record_error, "; THE COMMIT HAPPENED" if kind == "applied" else ""))
    return result


def refuse(o, check: str, message: str):
    o.fail([check])
    raise SystemExit("REFUSED: " + message)


def refuse_interpreter(o, check: str, message: str):
    """Distinct from every other refusal and from every gate code: exit EXIT_INTERPRETER (92), its own check name in outcome.json, before any connection."""
    o.fail([check])
    o._warn("REFUSED (interpreter): " + message + "\n")
    raise SystemExit(EXIT_INTERPRETER)


def interpreter_precheck(o, evidence_root, expect_evidence: str, log: list) -> None:
    """--apply, BEFORE the credential is fetched: find the dry run(s) whose outcome.json says status dry_run and whose evidence_digest equals --expect-evidence
    (they sit in the same evidence root) and compare their recorded runtime with this process. A record missing any field = cannot compare = REFUSED; any
    difference (interpreter path, full sys.version, psycopg, libpq) = REFUSED. No dry-run evidence found here (e.g. copied from another host): no early
    verdict; the evidence digest itself binds the runtime (run_leg), so a different interpreter still fails evidence_digest_matches_expected."""
    now, matches = runtime_record(), []
    try:
        entries = sorted(pathlib.Path(evidence_root).iterdir())
    except OSError:
        entries = []
    for d in entries:
        try:
            body = json.loads((d / "outcome.json").read_text())
        except (OSError, ValueError):
            continue
        if isinstance(body, dict) and body.get("status") == "dry_run" and body.get("evidence_digest") == expect_evidence:
            matches.append((d.name, body))
    if not matches:
        log.append(f"interpreter check: no dry-run evidence for this digest under {evidence_root}; the evidence digest itself binds the interpreter")
        return
    for name, body in matches:
        missing = [k for k in RUNTIME_KEYS if body.get(k) in (None, "")]
        if missing:
            refuse_interpreter(o, "dry_run_evidence_lacks_interpreter_record", f"cannot compare: the dry run {name} recorded no {', '.join(missing)} "
                               "(an older executor, or an edited file); repeat the dry run with this executor and use its evidence digest")
        differs = [k for k in RUNTIME_KEYS if body[k] != now[k]]
        if differs:
            refuse_interpreter(o, "interpreter_differs_from_dry_run", f"the dry run {name} used a different interpreter or driver ("
                               + "; ".join(f"{k}: dry run {body[k]!r}, now {now[k]!r}" for k in differs)
                               + "): run the apply with the SAME interpreter, or repeat the dry run under this one")
    log.append(f"interpreter check: {len(matches)} dry run(s) with this digest used the same interpreter, psycopg and libpq")


_HELD_SIGNALS = {signal.SIGTERM, signal.SIGHUP, signal.SIGINT}


def _on_terminate(signum, frame):
    raise SystemExit(128 + signum)


def install_signal_handlers() -> None:
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _on_terminate)


def execute(args, connect, now=None, gate_fp=None):
    """Returns (exit_code, result). `connect` is the only door to a database and is called ONLY after the plan hash matched."""
    now = now or dt.datetime.now(dt.timezone.utc)
    es = standards()
    evidence_root = resolve_evidence_root(getattr(args, "evidence_root", None))
    sha = exec_sha()
    phash = plan_hash(sha)
    gate_fp = gate_fp or dict(es.fingerprint(str(gate_dir())), under_test=False)
    try:
        run_dir = make_run_dir(evidence_root, args.mode, now.strftime("%Y%m%dT%H%M%S%fZ"))
    except EvidenceError as exc:
        return 1, {"status": "ABORTED_ROLLED_BACK", "reason": str(exc), "plan_hash": phash, "executor_sha256": sha}
    with safe_outcome_class(es)(run_dir, __file__, phash, gate_fp) as o:
        o.extra = outcome_extra(None, None, [])
        if args.expect_plan != phash:
            refuse(o, "args_expect_plan_mismatch", "--expect-plan does not equal the plan hash")
        if args.mode == "apply" and not args.expect_evidence:
            refuse(o, "args_expect_evidence_missing", "--apply requires --expect-evidence <digest from the matching dry run>")
        try:
            leg = forward_leg()
            parse_steps(leg.text())
        except (ValueError, OSError) as exc:
            refuse(o, "sql_file_unreadable_or_malformed", f"the SQL leg cannot be loaded ({type(exc).__name__})")
        lines: list[str] = []
        if args.mode == "apply":
            interpreter_precheck(o, evidence_root, args.expect_evidence, lines)
        conn = connect()                         # the administrator credential is fetched here, never earlier
        try:
            try:
                res = run_leg(conn, leg, "dry-run" if args.mode == "dry-run" else args.mode, lines.append)
            except Exception:
                conn.rollback()
                raise
            ck, digest = res["checks"], res["evidence_digest"]
            o.extra = res["outcome_extra"]
            if args.mode == "apply" and digest != args.expect_evidence:
                ck.chk("evidence_digest_matches_expected", False, "the evidence digest of this run differs from --expect-evidence")
                res["commit_ok"] = False
            result = {"plan_hash": phash, "executor_sha256": sha, "mode": args.mode, "evidence_digest": digest,
                      "failed_checks": ck.failed, "checks": {n: ok for n, ok, _ in ck.items}, "runtime": runtime_record(),
                      "deleted_ids": res["deleted_ids"], "rows_deleted_in_transaction": len(res["deleted_ids"]),
                      "chart_total_before": (res["pre_measure"] or {}).get("chart_total"), "chart_total_after": (res["post_measure"] or {}).get("chart_total"),
                      "other_charts_before": (res["pre_measure"] or {}).get("other_by_chart"), "other_charts_after": (res["post_measure"] or {}).get("other_by_chart"),
                      "deleted_rows_nonprivate_fingerprint_sha256": (res["pre_measure"] or {}).get("match_fingerprint"), "restore": RESTORE_NOTE,
                      "details": {n: d for n, ok, d in ck.items if d and not ok}, "log": lines + res["report"], "evidence_dir": str(run_dir)}
            if args.mode == "apply" and res["commit_ok"]:
                signal.pthread_sigmask(signal.SIG_BLOCK, _HELD_SIGNALS)       # SIGTERM/SIGHUP/SIGINT wait until the COMMIT is recorded
                try:
                    try:
                        conn.commit()
                    except BaseException as exc:                              # the commit call ITSELF failed: the server may have committed
                        o.mark_commit_unknown(digest, type(exc).__name__)
                        raise
                    o.mark_committed(digest)                                  # IMMEDIATELY after the commit
                finally:
                    signal.pthread_sigmask(signal.SIG_UNBLOCK, _HELD_SIGNALS)
                result["status"] = "COMMITTED"
                write_evidence(run_dir, res, result)
                return 0, conclude(o, result, "applied", digest)
            conn.rollback()
            if args.mode == "apply":
                result["status"] = "REFUSED_ROLLED_BACK"
                write_evidence(run_dir, res, result)
                return 1, conclude(o, result, "failed", digest, ck.failed)
            good = res["commit_ok"] if args.mode != "count" else not ck.failed
            result["status"] = ("COUNT_READ_ONLY_OK" if args.mode == "count" else "DRY_RUN_ROLLED_BACK_ALL_CHECKS_HOLD") if good else \
                ("COUNT_REFUSED" if args.mode == "count" else "DRY_RUN_ROLLED_BACK_REFUSED")
            write_evidence(run_dir, res, result)
            if good:
                return 0, conclude(o, result, "dry_run", digest)
            return 2, conclude(o, result, "failed", digest, ck.failed)
        finally:
            conn.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    for m in MODES:
        g.add_argument("--" + m, action="store_const", const=m, dest="mode")
    p.add_argument("--expect-plan")
    p.add_argument("--expect-evidence")
    p.add_argument("--evidence-root", default=None, help=f"ignored unless {TEST_EVIDENCE_ENV} is set (tests only)")
    return p


def parse_args(argv):
    p = build_parser()
    a = p.parse_args(argv)
    if not a.expect_plan:
        p.error("every mode requires --expect-plan <sha256> (the credential is fetched only for a named plan hash)")
    if a.mode == "apply" and not a.expect_evidence:
        p.error("--apply requires --expect-evidence <digest printed by the matching dry run>")
    return a


def refuse_under_test_outside_pytest(gate_fp, environ=None):
    """An under_test launch marker (run_gated.sh started with GATE_V2_UNDER_TEST=1) is for the test harness only: the executor refuses it,
    in EVERY mode including --dry-run, unless PYTEST_CURRENT_TEST is set."""
    environ = os.environ if environ is None else environ
    if gate_fp.get("under_test") and PYTEST_ENV not in environ:
        sys.stderr.write("REFUSED: the launch marker says the gate ran under test (GATE_V2_UNDER_TEST=1): the executor does not run against a "
                         "database from such a launch outside a pytest run. Start it through run_gated.sh without the test flag.\n")
        raise SystemExit(EXIT_NO_LAUNCH)


def main(argv=None) -> int:
    gate_fp = launch_gate()                  # FIRST: before the arguments are even parsed
    refuse_under_test_outside_pytest(gate_fp)
    args = parse_args(sys.argv[1:] if argv is None else argv)
    install_signal_handlers()
    try:
        code, result = execute(args, connect_admin, gate_fp=gate_fp)
    except SystemExit:
        raise
    except Exception as exc:
        print("failed: %s %s" % (type(exc).__name__, str(exc)[:200].replace("\n", " ")))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return code


if __name__ == "__main__":
    sys.exit(main())
