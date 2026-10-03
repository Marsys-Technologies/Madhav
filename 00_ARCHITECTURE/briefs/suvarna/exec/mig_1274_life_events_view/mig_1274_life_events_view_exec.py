#!/usr/bin/env python3
"""Owner-path executor for migration 1274: the chart-scoped, read-only, security-barrier view `public.life_events_chart_scoped`
(SS ruling N-105). DRAFT, HELD, NEVER RUN against any real system by its author, NEVER APPLIED.

WHAT IT DOES (forward leg), in ONE transaction as the Cloud SQL administrator (`postgres`: CREATEROLE, not a superuser), COMMIT only if every check holds:
  s1  GRANT the administrator membership of data_plane_schema_owner / amjis_app / data_plane_builder (only those it lacks; revoked again in s9)
  s2  preconditions (SQL, raising): life_events owner amjis_app, RLS off, the seven exposed columns and types, app_chart_context() is the G1c accessor,
      data_plane_builder holds NO privilege on life_events, schema public owned by data_plane_schema_owner, amjis_app has no CREATE on it, pre-images taken
  s3  data_plane_schema_owner: GRANT CREATE ON SCHEMA public TO amjis_app          (transient: one statement's worth)
  s4  amjis_app (the table owner): CREATE VIEW ... WITH (security_barrier = true) ... WHERE chart_id = app_chart_context(); REVOKE ALL FROM PUBLIC,
      retrieval_census_ro (the default ACL of amjis_app in public would otherwise grant it); GRANT SELECT TO data_plane_builder
  s5  data_plane_schema_owner: REVOKE CREATE ON SCHEMA public FROM amjis_app
  s6/s7  behavioural probe (COUNTS only, never content): as the builder the table is unreadable; the view returns 0 rows with the GUC unset, malformed, or
         pointing at a chart with no events; exactly the pinned chart's rows for the probe chart (and a second chart when one exists); read-only
  s8  ASSERTING post-checks (RAISE, never WARN): the grant took (has_table_privilege), builder has SELECT only, view ACL exactly {owner, builder SELECT},
      security_barrier only, no direct builder privilege on life_events, schema/table ACLs byte-identical to the pre-image, accessor unchanged
  s9  revoke the memberships granted in s1
and, independently of those SQL assertions, the executor re-reads the catalog and applies its own commit conditions (check names below).
The exact inverse is the rollback leg (DROP VIEW as the owner, same discipline).

MODES (every mode needs --expect-plan: the in-process administrator credential is fetched only for a plan hash the operator names)
  --count                          read-only catalog preconditions + pre-state, no role switch, always ROLLBACK
  --dry-run                        apply everything, run every commit condition, print the evidence digest, ROLLBACK
  --apply --expect-plan H --expect-evidence D
                                   same transaction; COMMIT only if every check holds and D equals this run's evidence digest
  --rollback-dry-run / --rollback --expect-plan H --expect-evidence D      the inverse

LAUNCH (GATE_V2). Never started directly: `exec/gate_v2/run_gated.sh <python3.11> mig_1274_life_events_view_exec.py <args>`. main() calls launch_gate() FIRST
and refuses (exit 93) without a verifying GATE_V2_LAUNCH marker. --apply / --rollback refuse (exit 92, before any connection) under a different interpreter or
driver than the matching dry run (the runtime record is bound into the evidence digest as well). outcome.json is written in every mode and status; a MISSING
outcome.json means check the database. The administrator password is fetched from Secret Manager inside this process ONLY after the plan hash matched, never
printed or saved; tests inject a disposable connection and never reach connect_admin(). The source runs on Python 3.11 and 3.12+.
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
SQL_FORWARD = HERE / "1274_life_events_chart_scoped_view.sql"
SQL_ROLLBACK = HERE / "1274_life_events_chart_scoped_view_ROLLBACK.sql"
EVIDENCE_ROOT = "/Users/Dev/suvarna-evidence/MigLifeEvents1274"

VIEW_NAME = "life_events_chart_scoped"
TABLE_NAME = "life_events"
SCHEMA = "public"
OWNER_ROLE = "amjis_app"
SCHEMA_OWNER = "data_plane_schema_owner"
BUILDER = "data_plane_builder"
ASSUMED_FORWARD = (SCHEMA_OWNER, OWNER_ROLE, BUILDER)
ASSUMED_ROLLBACK = (SCHEMA_OWNER, OWNER_ROLE)
VIEW_COLUMNS = ("id", "event_id", "event_date", "category", "domain", "outcome_observed", "chart_id")      # 7: no free text (SS N-109)
# sha256 of pg_get_viewdef(view) with whitespace collapsed, as measured on the PostgreSQL 15.17 mirror (the text is stable within a major version); a different text on production (a different minor
# version) fails the commit condition `post_view_definition_equals_plan` at the DRY RUN, before any apply.
VIEW_DEF_SHA256 = "df02c05e9dd989f99e0f7e8fef6d5b0c5b317df1227bcc38cb6fabae30aa164d"


# ------------------------------------------------------------------------------------------------------ gate wiring (GATE_V2)
GATE_TBD = "TBD_BIND_AT_GATE_REVISION_3"        # the marker for an UNBOUND pin: launch_gate refuses while any pin is this value
# BOUND by SS decision N-86 to GATE_V2 revision 3 (PR #2938 head 7f0db55c371fe13ddccc493ac0730c8703a7e940), after the sha256 of the three files at that commit
# were recomputed (git show <commit>:<path> | shasum -a 256) and found equal. tests/gate_fixture holds byte-identical copies and a test proves it.
GATE_PINS = {"prerun_gate.py": "01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e",
             "run_gated.sh": "305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076",
             "executor_standards.py": "bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135"}
GATE_DIR_ENV = "M1274_TEST_GATE_DIR"
TEST_EVIDENCE_ENV = "M1274_TEST_EVIDENCE_ROOT"
PYTEST_ENV = "PYTEST_CURRENT_TEST"
EXIT_NO_LAUNCH = 93
EXIT_TEST_ENV = 95
EXIT_INTERPRETER = 92        # --apply / --rollback under a different interpreter (or driver) than the dry run, or no comparable record (free: the gate uses 1, 2, 64, 93-98, 128+n)
MODES = ("count", "dry-run", "apply", "rollback-dry-run", "rollback")


def gate_dir(environ=None) -> pathlib.Path:
    """exec/gate_v2 next to this folder. M1274_TEST_GATE_DIR (tests only) is REFUSED, exit 95, outside a pytest run."""
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
        _STD[str(d)] = _load("executor_standards_" + str(len(_STD)), d / "executor_standards.py")
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
        sys.stderr.write("REFUSED: the GATE_V2 pins in this executor are TBD (gate revision 3 not yet bound): the plan hash is PROVISIONAL "
                         "and this executor cannot run.\n")
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




# ---------------------------------------------------------------------------------------------------------------------- SQL legs
@dataclasses.dataclass(frozen=True)
class Leg:
    name: str                 # forward | rollback
    sql_path: pathlib.Path
    assumed: tuple            # roles the leg makes the administrator a member of (revoked again by the leg's last step)

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
    return Leg("forward", SQL_FORWARD, ASSUMED_FORWARD)


def rollback_leg() -> Leg:
    return Leg("rollback", SQL_ROLLBACK, ASSUMED_ROLLBACK)


# commit conditions the EXECUTOR re-derives from the catalog (independently of the asserting SQL in the steps)
FORWARD_CHECKS = (
    "pre_roles_exist", "pre_table_owner_and_rls", "pre_view_absent", "pre_builder_has_no_table_privilege", "pre_schema_owner",
    "pre_owner_role_has_no_create_on_public", "pre_accessor_function_present", "pre_admin_can_assume_the_roles",
    "step_*", "post_view_is_a_plain_security_barrier_view_owned_by_the_table_owner", "post_view_definition_equals_plan",
    "post_builder_select_on_view", "post_builder_select_only_on_view", "post_view_acl_is_exactly_owner_plus_builder_select",
    "post_builder_has_no_table_privilege", "post_table_acl_unchanged", "post_schema_acl_unchanged",
    "post_owner_role_has_no_create_on_public", "post_accessor_function_unchanged", "post_memberships_restored",
)
ROLLBACK_CHECKS = (
    "pre_roles_exist", "pre_view_present", "pre_admin_can_assume_the_roles", "step_*", "post_view_absent",
    "post_builder_has_no_table_privilege", "post_table_acl_unchanged", "post_schema_acl_unchanged",
    "post_accessor_function_unchanged", "post_memberships_restored",
)


def render_plan(sha: str | None = None, pins: dict | None = None) -> str:
    pins = pins or GATE_PINS
    sha = sha or exec_sha()
    f, r = forward_leg(), rollback_leg()
    lines = [
        "PLAN mig_1274_life_events_view (SS ruling N-105): chart-scoped, read-only, security-barrier view over life_events for data_plane_builder",
        f"object: {SCHEMA}.{VIEW_NAME} WITH (security_barrier = true); columns: {', '.join(VIEW_COLUMNS)}; owner {OWNER_ROLE}; SELECT to {BUILDER} ONLY",
        f"scoping: chart_id = {SCHEMA}.app_chart_context() (GUC app.chart_context; unset or malformed = NULL = zero rows)",
        "accepted limit (SS N-109): the scoping stops ACCIDENTAL cross-chart reads, not a HOSTILE builder session (the GUC is session-settable); no free-text column is exposed",
        f"transaction: ONE, as the Cloud SQL administrator; SET LOCAL lock_timeout = {LOCK_TIMEOUT}, statement_timeout = {STATEMENT_TIMEOUT}; COMMIT only if every check holds",
        f"view definition sha256 (whitespace collapsed): {VIEW_DEF_SHA256}",
        f"forward commit conditions: {', '.join(FORWARD_CHECKS)}",
        f"rollback commit conditions: {', '.join(ROLLBACK_CHECKS)}",
        f"-- forward sql: {SQL_FORWARD.name} sha256 {f.sql_sha256}",
    ]
    for n, s in f.steps:
        lines += [f"-- step {n}", s.rstrip("\n")]
    lines.append(f"-- rollback sql: {SQL_ROLLBACK.name} sha256 {r.sql_sha256}")
    for n, s in r.steps:
        lines += [f"-- step {n}", s.rstrip("\n")]
    lines += [f"-- gate pin {k}: {v}" for k, v in sorted(pins.items())]
    lines.append(f"-- executor: mig_1274_life_events_view_exec.py sha256 {sha}")
    return "\n".join(lines)


def plan_hash_unbound(sha: str | None = None, pins: dict | None = None) -> str:
    return hashlib.sha256((render_plan(sha, pins) + "\n").encode()).hexdigest()


def plan_hash(sha: str | None = None, pins: dict | None = None, environ=None) -> str:
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
    return psycopg.connect(host="127.0.0.1", port=5433, dbname="amjis", user="postgres",
                           password=secret("cloudsql-postgres-admin-password"), sslmode="disable", connect_timeout=15)


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=lambda s: sorted(s) if isinstance(s, (set, frozenset)) else str(s))


def one(cur, sql: str, params=None):
    cur.execute(sql, params)
    row = cur.fetchone()
    return None if row is None else (row[0] if len(row) == 1 else tuple(row))


_REL = ("FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = %s AND c.relname = %s")
ROLES_USED = (SCHEMA_OWNER, OWNER_ROLE, BUILDER, "retrieval_census_ro")


def snap(cur) -> dict:
    """The catalog facts the plan reasons about, read WITHOUT any role switch (pure pg_catalog queries: no USAGE on public is needed)."""
    d: dict = {}
    d["who"] = one(cur, "SELECT current_user::text, (SELECT rolsuper FROM pg_roles WHERE rolname = current_user), "
                        "(SELECT rolcreaterole FROM pg_roles WHERE rolname = current_user), current_setting('server_version_num')::int")
    d["roles_exist"] = {r: bool(one(cur, "SELECT count(*) FROM pg_roles WHERE rolname = %s", (r,))) for r in ROLES_USED}
    d["role_is_super"] = {r: bool(one(cur, "SELECT COALESCE((SELECT rolsuper FROM pg_roles WHERE rolname = %s), false)", (r,))) for r in ROLES_USED}
    d["memberships"] = {r: bool(one(cur, "SELECT pg_has_role(current_user, %s, 'MEMBER')", (r,))) for r in ASSUMED_FORWARD
                        if d["roles_exist"].get(r)}
    d["schema"] = one(cur, "SELECT pg_get_userbyid(nspowner)::text, COALESCE(nspacl::text, 'NULL') FROM pg_namespace WHERE nspname = %s", (SCHEMA,))
    d["owner_create_on_public"] = bool(one(cur, "SELECT has_schema_privilege(%s, %s, 'CREATE')", (OWNER_ROLE, SCHEMA))) if d["roles_exist"][OWNER_ROLE] else None
    d["table"] = one(cur, "SELECT pg_get_userbyid(c.relowner)::text, COALESCE(c.relacl::text, 'NULL'), c.relrowsecurity, c.relforcerowsecurity " + _REL,
                     (SCHEMA, TABLE_NAME))
    d["builder_on_table"] = one(cur, "SELECT has_table_privilege(%s, c.oid, 'SELECT'), "
                                     "has_table_privilege(%s, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER'), "
                                     "has_any_column_privilege(%s, c.oid, 'SELECT,INSERT,UPDATE,REFERENCES') " + _REL,
                                (BUILDER, BUILDER, BUILDER, SCHEMA, TABLE_NAME)) if d["roles_exist"][BUILDER] else None
    d["view"] = one(cur, "SELECT c.relkind::text, pg_get_userbyid(c.relowner)::text, COALESCE(c.reloptions::text, ''), "
                         "encode(sha256(convert_to(regexp_replace(pg_get_viewdef(c.oid), '\\s+', ' ', 'g'), 'UTF8')), 'hex') " + _REL,
                    (SCHEMA, VIEW_NAME))
    if d["view"] is not None and d["roles_exist"][BUILDER]:
        d["builder_on_view"] = one(cur, "SELECT has_table_privilege(%s, c.oid, 'SELECT'), "
                                        "has_table_privilege(%s, c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER') " + _REL,
                                   (BUILDER, BUILDER, SCHEMA, VIEW_NAME))
        cur.execute("SELECT (CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE pg_get_userbyid(a.grantee)::text END) || ':' || a.privilege_type || ':' || a.is_grantable::text || ':' || "
                    "pg_get_userbyid(a.grantor)::text FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace, "
                    "LATERAL aclexplode(c.relacl) a WHERE n.nspname = %s AND c.relname = %s ORDER BY 1", (SCHEMA, VIEW_NAME))
        d["view_acl"] = [r[0] for r in cur.fetchall()]
    else:
        d["builder_on_view"], d["view_acl"] = None, []
    d["fn_md5"] = one(cur, "SELECT md5(pg_get_functiondef(p.oid)) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
                           "WHERE n.nspname = %s AND p.proname = 'app_chart_context' AND p.pronargs = 0", (SCHEMA,))
    return d


def owner_default_acl(cur) -> list:
    """The ACL a fresh relation of OWNER_ROLE has before any grant: acldefault('r', owner)."""
    cur.execute("SELECT pg_get_userbyid(a.grantee)::text || ':' || a.privilege_type || ':' || a.is_grantable::text || ':' || pg_get_userbyid(a.grantor)::text "
                "FROM aclexplode(acldefault('r', (SELECT oid FROM pg_roles WHERE rolname = %s))) a ORDER BY 1", (OWNER_ROLE,))
    return [r[0] for r in cur.fetchall()]


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
    who = pre["who"]
    need = ROLES_USED if leg.name == "forward" else (SCHEMA_OWNER, OWNER_ROLE)
    ck.chk("pre_roles_exist", all(pre["roles_exist"].get(r) for r in need), {r: pre["roles_exist"].get(r) for r in need})
    can = all(pre["memberships"].get(r) or (who[2] and not pre["role_is_super"].get(r) and pre["roles_exist"].get(r)) for r in leg.assumed) \
        and (who[3] < 160000 or bool(who[1]))
    ck.chk("pre_admin_can_assume_the_roles", can, f"admin={who[0]} super={who[1]} createrole={who[2]} server_version_num={who[3]}")
    ck.chk("pre_accessor_function_present", pre["fn_md5"] is not None)
    if leg.name == "forward":
        t = pre["table"]
        ck.chk("pre_table_owner_and_rls", t is not None and t[0] == OWNER_ROLE and t[2] is False and t[3] is False, None if t is None else (t[0], t[2], t[3]))
        ck.chk("pre_view_absent", pre["view"] is None)
        bt = pre["builder_on_table"]
        ck.chk("pre_builder_has_no_table_privilege", bt is not None and not any(bt), bt)
        ck.chk("pre_schema_owner", pre["schema"] is not None and pre["schema"][0] == SCHEMA_OWNER, pre["schema"] and pre["schema"][0])
        ck.chk("pre_owner_role_has_no_create_on_public", pre["owner_create_on_public"] is False, pre["owner_create_on_public"])
    else:
        ck.chk("pre_view_present", pre["view"] is not None)


def post_checks(leg: Leg, pre: dict, post: dict, ck: Checks, expected_owner_acl: list) -> None:
    ck.chk("post_table_acl_unchanged", post["table"] == pre["table"])
    ck.chk("post_schema_acl_unchanged", post["schema"] == pre["schema"], None if post["schema"] == pre["schema"] else "schema public ACL differs from the pre-image")
    ck.chk("post_accessor_function_unchanged", post["fn_md5"] == pre["fn_md5"] and post["fn_md5"] is not None)
    ck.chk("post_memberships_restored", post["memberships"] == pre["memberships"], {"pre": pre["memberships"], "post": post["memberships"]})
    bt = post["builder_on_table"]
    ck.chk("post_builder_has_no_table_privilege", bt is not None and not any(bt), bt)
    if leg.name == "rollback":
        ck.chk("post_view_absent", post["view"] is None)
        return
    ck.chk("post_owner_role_has_no_create_on_public", post["owner_create_on_public"] is False, post["owner_create_on_public"])
    v = post["view"]
    ck.chk("post_view_is_a_plain_security_barrier_view_owned_by_the_table_owner",
           v is not None and v[0] == "v" and v[1] == OWNER_ROLE and v[2] == "{security_barrier=true}", None if v is None else (v[0], v[1], v[2]))
    ck.chk("post_view_definition_equals_plan", v is not None and v[3] == VIEW_DEF_SHA256, None if v is None else v[3])
    bv = post["builder_on_view"]
    ck.chk("post_builder_select_on_view", bv is not None and bv[0] is True, bv)
    ck.chk("post_builder_select_only_on_view", bv is not None and bv[0] is True and bv[1] is False, bv)
    want = sorted(expected_owner_acl + [f"{BUILDER}:SELECT:false:{OWNER_ROLE}"])
    ck.chk("post_view_acl_is_exactly_owner_plus_builder_select", sorted(post["view_acl"]) == want, {"got": post["view_acl"], "want": want})


def read_counts(cur) -> dict:
    """Row COUNTS recorded by the probe steps (never content); reported, not part of the evidence digest."""
    out = {}
    for k in ("probe_n", "other_n", "total_n"):
        cur.execute("SELECT current_setting(%s, true)", ("madhav.m1274_" + k,))
        out[k] = cur.fetchone()[0]
    return out


def run_leg(conn, leg: Leg, mode: str, out) -> dict:
    """mode: count (catalog only, nothing executed) | dry-run | apply | rollback-dry-run | rollback. Returns the checks, the evidence digest and commit_ok;
    the CALLER commits or rolls back."""
    ck = Checks()
    cur = conn.cursor()
    cur.execute(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'")
    cur.execute(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT}'")
    pre = snap(cur)
    pre_checks(leg, pre, ck)
    expected_owner_acl = owner_default_acl(cur) if pre["roles_exist"].get(OWNER_ROLE) else []
    post, counts = None, {}
    if mode != "count" and not ck.failed:
        for name, sql in leg.steps:
            out(f"step {name}")
            try:
                cur.execute(sql)
            except psycopg.Error as exc:
                ck.chk("step_" + name, False, f"{type(exc).__name__} {getattr(exc.diag, 'sqlstate', None)}: {getattr(exc.diag, 'message_primary', '')}")
                break
            ck.chk("step_" + name, True)
        else:
            if leg.name == "forward":
                counts = read_counts(cur)
            post = snap(cur)
            post_checks(leg, pre, post, ck, expected_owner_acl)
    parts = {"leg": leg.name, "sql_sha256": leg.sql_sha256, "pre": pre, "post": post, "expected_owner_acl": expected_owner_acl,
             "checks": [[n, ok] for n, ok, _ in ck.items], "runtime": runtime_record()}
    digest = hashlib.sha256(canonical(parts).encode()).hexdigest()
    commit_ok = mode != "count" and post is not None and not ck.failed
    report = [f"leg {leg.name} mode {mode}"] + [f"  {'ok  ' if ok else 'FAIL'} {n}" + (f"  ({d})" if d and not ok else "") for n, ok, d in ck.items]
    if counts:
        report.append(f"  counts (not part of the digest): {counts}")
    return {"checks": ck, "evidence_digest": digest, "commit_ok": commit_ok, "pre": pre, "post": post, "counts": counts, "report": report,
            "digest_parts": parts}


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
    """WHICH interpreter and driver is running: sys.executable, the full sys.version, psycopg.__version__ and the libpq version (an int, e.g.
    170002). Recorded in outcome.json (every status) and in result.json, and BOUND INTO THE EVIDENCE DIGEST (run_leg): the dry run and the apply
    must use the SAME interpreter and driver, and the apply refuses by itself otherwise (interpreter_precheck, then the digest)."""
    return {"python_executable": sys.executable, "python_version": sys.version, "psycopg_version": psycopg.__version__,
            "libpq_version": psycopg.pq.version()}


def add_interpreter_to_outcome(path):
    """Adds runtime_record() to outcome.json, in every status. The gate's executor_standards.py is pinned byte-for-byte (GATE_PINS), so the
    fields are added here, atomically (temp file + os.replace in the same directory, mode 0600), right after the standard write."""
    with open(path) as f:
        body = json.load(f)
    body.update(runtime_record())
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
    """executor_standards.outcome_guard whose own file write can never mask the real result, with a committed flag: after COMMIT an
    interruption records `applied` with a warning, never `failed`."""
    if id(es) in _SAFE_CLASS:
        return _SAFE_CLASS[id(es)]

    class SafeOutcome(es.outcome_guard):
        write_error = None
        interpreter_record_error = None        # the standard outcome.json exists but the interpreter record could not be added
        committed = False
        commit_unknown = None              # class name of the exception conn.commit() itself raised: the server MAY have committed
        commit_digest = None

        def mark_committed(self, digest):
            """Called IMMEDIATELY after conn.commit(): from here on the truth is `applied`, whatever happens next."""
            self.committed, self.commit_digest = True, digest

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
                add_interpreter_to_outcome(self.path)
            except Exception as exc:        # the standard file exists but lacks the interpreter record: reported as exactly that, never a crash after COMMIT
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
                self._warn("WARNING: COMMIT STATE UNKNOWN (%s raised by commit()): the change may or may not be committed. outcome.json records "
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
                "outcome.json written without the interpreter record (%s)%s" % (o.interpreter_record_error, "; THE COMMIT HAPPENED" if kind == "applied" else ""))
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
    """--apply / --rollback, BEFORE the credential is fetched: find the dry run(s) whose outcome.json says status dry_run and whose
    evidence_digest equals --expect-evidence (they sit in the same evidence root) and compare their recorded runtime with this process.
    A record missing any field = cannot compare = REFUSED; any difference (interpreter path, full sys.version, psycopg, libpq) = REFUSED.
    No dry-run evidence found here (e.g. copied from another host): no early verdict; the evidence digest itself binds the runtime
    (run_leg), so a different interpreter still fails evidence_digest_matches_expected."""
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
        if args.expect_plan != phash:
            refuse(o, "args_expect_plan_mismatch", "--expect-plan does not equal the plan hash")
        if args.mode in ("apply", "rollback") and not args.expect_evidence:
            refuse(o, "args_expect_evidence_missing", f"--{args.mode} requires --expect-evidence <digest from the matching dry run>")
        try:
            leg = rollback_leg() if args.mode.startswith("rollback") else forward_leg()
            parse_steps(leg.text())
        except (ValueError, OSError) as exc:
            refuse(o, "sql_file_unreadable_or_malformed", f"the SQL leg cannot be loaded ({type(exc).__name__})")
        lines: list[str] = []
        if args.mode in ("apply", "rollback"):
            interpreter_precheck(o, evidence_root, args.expect_evidence, lines)
        conn = connect()                         # the administrator credential is fetched here, never earlier
        try:
            try:
                res = run_leg(conn, leg, "dry-run" if args.mode in ("dry-run", "rollback-dry-run") else args.mode, lines.append)
            except Exception:
                conn.rollback()
                raise
            ck, digest = res["checks"], res["evidence_digest"]
            if args.mode in ("apply", "rollback") and digest != args.expect_evidence:
                ck.chk("evidence_digest_matches_expected", False, "the evidence digest of this run differs from --expect-evidence")
                res["commit_ok"] = False
            result = {"plan_hash": phash, "executor_sha256": sha, "mode": args.mode, "evidence_digest": digest,
                      "failed_checks": ck.failed, "checks": {n: ok for n, ok, _ in ck.items}, "runtime": runtime_record(),
                      "counts": res["counts"], "details": {n: d for n, ok, d in ck.items if d and not ok}, "log": lines + res["report"],
                      "evidence_dir": str(run_dir)}
            if args.mode in ("apply", "rollback") and res["commit_ok"]:
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
            if args.mode in ("apply", "rollback"):
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
    if a.mode in ("apply", "rollback") and not a.expect_evidence:
        p.error(f"--{a.mode} requires --expect-evidence <digest printed by the matching dry run>")
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
