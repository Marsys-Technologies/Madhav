"""Suvarṇa Monitor — the environment checker for the autonomous campaign.

    python -m suvarna_tracker.monitor [--once | --watch SECONDS] [--emit] [--repair] [--notify] [--json]

Twelve checks decide whether the environment the campaign runs in is sound: the DB proxy port, the
read-only credential file's permissions, whether the credential can actually write (review #16 —
permissions alone don't prove the DB role itself is read-only), the laptop's power state, whether
sleep is prevented, the hold switch, free disk space, the tracker's own health endpoint, whether
either interim runtime session's Conductor is still heartbeating (L.15), whether the swarm is
running isolated from the native's own account (``isolation``, CODE-12), whether the decisions log
carries a line written by anyone other than Strategic Suvarṇa (``decision_writers``, CODE-13), and
whether the builder's own authenticated scope matches its provisioning record (``builder_scope``,
CODE-15). Each returns ``ok`` / ``warn`` / ``block``; the overall status is the worst of the twelve,
and the process exit code mirrors it (0 / 1 / 2) so this doubles as a CI-style gate.

Design rules:
- **Never fabricate a pass.** A check that cannot measure reports ``warn`` with the reason, never
  ``ok`` (CLAUDE.md §N.8 — a signal without a real detector behind it is null, not green).
- **Never read the credential file's contents.** The credential check only ``os.stat``s it; it never
  opens it, and never prints anything beyond the path-free facts an operator needs (mode, existence).
- **Conservative repair.** ``--repair`` only starts a process that is verifiably not already running,
  and never touches hold / credential / disk / power — those need a human. The hold switch, when on,
  suppresses every repair action, not only the ones it names explicitly.
- **Injectable everything that touches the outside world.** ``Config`` carries the port numbers, the
  paths, and every subprocess/HTTP/disk helper as fields with real defaults, so tests can swap in
  fakes without any real network call beyond 127.0.0.1 and without spawning any real process.
- **A failed or blocked notification never fails the monitor.** ``--notify`` shares ``--emit``'s own
  change-dedupe (``monitor_state.json``'s ``non_ok`` field) so a native watching the Mac's notification
  centre sees exactly one alert per state change, not one every ``--watch`` tick.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import getpass
import json
import os
import shlex

# N-20 (native, 2026-09-29): the read-only credential lives in one file outside every repository,
# owner-only (mode 600). Tools default to it; its contents are never read or printed by these tools.
DEFAULT_PGENV = os.path.expanduser("~/.config/suvarna/pgenv.sh")
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass, field

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "suvarna_tracker"

from suvarna_tracker.decisions import default_path as _decisions_default_path  # noqa: E402
from suvarna_tracker.decisions import load_decisions  # noqa: E402
from suvarna_tracker.detectors import _run as _det_run  # noqa: E402
from suvarna_tracker.detectors import _suvarna_build_cmd as _det_suvarna_build_cmd  # noqa: E402
from suvarna_tracker.detectors import port_open as _det_port_open  # noqa: E402
from suvarna_tracker.detectors import power_source as _det_power_source  # noqa: E402
from suvarna_tracker.events import append, now_iso  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

CHECK_NAMES = ("db_proxy", "credential", "credential_readonly", "power", "sleep_prevented", "hold", "disk",
               "tracker", "conductor_heartbeat", "isolation", "decision_writers", "builder_scope")
STATUS_RANK = {"ok": 0, "warn": 1, "block": 2}

# CODE-13: the only writer a `decided` decisions-log line may carry (S2 — the Strategic Suvarṇa
# session, native present; a steward or any other actor's `decided` line is a conflict, not a
# second source of truth).
DECISIONS_ALLOWED_WRITER = "strategic-suvarna"

# CODE-15: the chart this builder identity is ever provisioned against (CLAUDE.md §B — canonical
# chart_id).
BUILDER_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# CODE-12: until N-25 (arch §2.4) actually stands up the separate macOS user, the expected user is
# configurable so the check's shape is ready the day it lands, without ever fabricating a pass in
# the meantime — see `check_isolation`.
ISOLATION_EXPECTED_USER_ENV = "SUVARNA_ISOLATION_EXPECTED_USER"

# L.15: default staleness threshold for the conductor_heartbeat check (arch §5.1's heartbeat-per-pass
# contract; three missed loop intervals is the watchdog's own relaunch threshold, arch §5.5 — a wider
# default here means this check warns before the watchdog would act, never after).
DEFAULT_CONDUCTOR_STALE_MIN = 45


# --------------------------------------------------------------------------------------------
# Default helpers (the real world). Every one of these is a Config field so tests can replace it.
# --------------------------------------------------------------------------------------------

def _default_run_fn(cmd: list[str] | str, timeout: int = 5) -> tuple[int, str]:
    return _det_run(cmd, timeout=timeout)


def _default_http_get(url: str, timeout: float = 3.0) -> tuple[int | None, str, str | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (127.0.0.1 only, by contract)
            return resp.status, resp.read().decode("utf-8", "replace"), None
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace") if exc.fp else ""
        return exc.code, body, None
    except Exception as exc:  # noqa: BLE001 — unreachable/timeout/etc. is data, not a crash
        return None, "", f"{type(exc).__name__}: {exc}"


def _default_launch(argv: list[str], cwd: str | None = None, log_path: str | None = None,
                    env: dict | None = None) -> None:
    """Start a detached process. Never waits; never raises out of the caller's control flow here —
    the caller (a _repair_* function) wraps this so a launch failure becomes a reported string, not
    a crash."""
    log_fh = open(log_path, "ab") if log_path else subprocess.DEVNULL
    try:
        subprocess.Popen(argv, cwd=cwd, stdout=log_fh, stderr=log_fh, stdin=subprocess.DEVNULL,
                         env=env, start_new_session=True, close_fds=True)
    finally:
        if log_path:
            log_fh.close()


def _default_credential_query_fn(pgenv: str, sql: str, timeout: int = 10) -> tuple[int, str, str]:
    """Run one read-only SQL query with the credential, sourced only inside this subprocess shell —
    the caller never opens, reads, or holds the file's contents in this Python process; every fact
    used comes from `psql`'s own stdout/stderr (Fix 3, review #16). Both the path and the SQL are
    ``shlex.quote``d (security review 2), and the SQL is prefixed with ``set search_path = pg_catalog;``
    so nothing in a user schema can shadow a catalog name; ``-q`` keeps the SET tag out of stdout."""
    full_sql = sql if sql.lstrip().lower().startswith("set search_path") else f"set search_path = pg_catalog; {sql}"
    cmd = (f"source {shlex.quote(pgenv)} && psql -q -X -t -A -v ON_ERROR_STOP=1 "
           f"-c {shlex.quote(full_sql)}")
    p = subprocess.run(["bash", "-c", cmd], timeout=timeout, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


_APPLESCRIPT_MAX_LEN = 200


def _default_notify(summary: str) -> None:
    """Fire a macOS notification via ``osascript``. Escapes backslash-then-quote (that order matters:
    escaping quotes first would double-escape the backslashes just inserted) so a check detail can
    never break out of the AppleScript string literal, truncates to a sane length, and never raises —
    a notification is a convenience, never a reason to fail the monitor."""
    safe = (summary or "").replace("\\", "\\\\").replace('"', '\\"')[:_APPLESCRIPT_MAX_LEN]
    script = f'display notification "{safe}" with title "Suvarṇa Monitor"'
    try:
        subprocess.run(["osascript", "-e", script], timeout=5, capture_output=True)
    except Exception:  # noqa: BLE001 — a failed notification must never fail the monitor
        pass


def _default_disk_free_bytes(path: str) -> float:
    p = os.path.abspath(path)
    while not os.path.exists(p):
        parent = os.path.dirname(p)
        if not parent or parent == p:
            p = "/"
            break
        p = parent
    st = os.statvfs(p)
    return float(st.f_frsize) * st.f_bavail


# --------------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------------

@dataclass
class Config:
    home: str
    pgenv: str | None = None
    db_port: int = 5433
    tracker_port: int = 8765
    tracker_host: str = "127.0.0.1"
    package_dir: str = HERE
    run_dir: str = ""
    hold_path: str = ""
    state_path: str = ""
    events_path: str = ""
    port_open_fn: Callable[[int], bool] | None = None
    power_source_fn: Callable[[], str] | None = None
    run_fn: Callable[..., tuple[int, str]] | None = None
    http_get_fn: Callable[[str, float], tuple[int | None, str, str | None]] | None = None
    launch_fn: Callable[..., None] | None = None
    disk_free_fn: Callable[[str], float] | None = None
    credential_query_fn: Callable[[str, str, int], tuple[int, str, str]] | None = None
    # None = read SUVARNA_READER_SECDEF_ALLOW at check time; tests pass an explicit frozenset.
    secdef_allowlist: frozenset[str] | None = None
    conductor_stale_min: int = DEFAULT_CONDUCTOR_STALE_MIN
    now_fn: Callable[[], "dt.datetime"] | None = None
    notify_fn: Callable[[str], None] | None = None
    # CODE-13: decisions log path (default mirrors decisions.default_path()'s own env/home rule).
    decisions_path: str = ""
    # CODE-12: expected user under N-25, and the injectable "who am I" function (real default:
    # getpass.getuser). None = read ISOLATION_EXPECTED_USER_ENV at check time.
    isolation_expected_user: str | None = None
    getuser_fn: Callable[[], str] | None = None
    # CODE-15: where the native's E7.2 provisioning record lives, and the full path to
    # `suvarna-build` (default mirrors detectors._suvarna_build_cmd()'s own env/default rule).
    builder_identity_path: str = ""
    suvarna_build_cmd: str = ""

    def __post_init__(self) -> None:
        self.run_dir = self.run_dir or os.path.join(self.home, "run")
        self.hold_path = self.hold_path or os.path.join(self.run_dir, "SUVARNA_HOLD")
        self.state_path = self.state_path or os.path.join(self.run_dir, "monitor_state.json")
        self.events_path = self.events_path or os.path.join(self.run_dir, "EVENTS.jsonl")
        self.decisions_path = self.decisions_path or os.environ.get("SUVARNA_DECISIONS") \
            or os.path.join(self.run_dir, "DECISIONS.jsonl")
        self.builder_identity_path = self.builder_identity_path or os.path.join(self.run_dir, "builder_identity.json")
        self.suvarna_build_cmd = self.suvarna_build_cmd or _det_suvarna_build_cmd()
        self.port_open_fn = self.port_open_fn or _det_port_open
        self.power_source_fn = self.power_source_fn or _det_power_source
        self.run_fn = self.run_fn or _default_run_fn
        self.http_get_fn = self.http_get_fn or _default_http_get
        self.launch_fn = self.launch_fn or _default_launch
        self.disk_free_fn = self.disk_free_fn or _default_disk_free_bytes
        self.credential_query_fn = self.credential_query_fn or _default_credential_query_fn
        self.now_fn = self.now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
        self.notify_fn = self.notify_fn or _default_notify
        self.getuser_fn = self.getuser_fn or getpass.getuser

    @property
    def tracker_stop_path(self) -> str:
        return os.path.join(self.run_dir, "TRACKER_STOP")


def default_config() -> Config:
    home = os.environ.get("SUVARNA_HOME", "/Users/Dev/suvarna")
    return Config(
        home=home,
        pgenv=os.environ.get("SUVARNA_PGENV") or DEFAULT_PGENV,
        db_port=int(os.environ.get("SUVARNA_DB_PORT", "5433")),
        tracker_port=int(os.environ.get("SUVARNA_TRACKER_PORT", "8765")),
        events_path=os.environ.get("SUVARNA_EVENTS", os.path.join(home, "run", "EVENTS.jsonl")),
        conductor_stale_min=int(os.environ.get("SUVARNA_CONDUCTOR_STALE_MIN", str(DEFAULT_CONDUCTOR_STALE_MIN))),
    )


@dataclass
class CheckResult:
    name: str
    status: str          # ok | warn | block
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


# --------------------------------------------------------------------------------------------
# The seven checks
# --------------------------------------------------------------------------------------------

def check_db_proxy(cfg: Config) -> CheckResult:
    if cfg.port_open_fn(cfg.db_port):
        return CheckResult("db_proxy", "ok", f"port {cfg.db_port} accepting connections")
    return CheckResult("db_proxy", "block", f"port {cfg.db_port} not accepting connections")


# Backups of the write-capable app-login credential belong in ~/.config/madhav-admin/, never beside
# the reader credential (security review 2, finding 1). Matched by NAME only; never opened.
STRAY_BACKUP_PATTERNS = ("pgenv*.bak*", "pgenv.previous*", ".pgenv.*.tmp")


def _stray_backups(pgenv: str) -> list[str]:
    try:
        names = os.listdir(os.path.dirname(os.path.abspath(pgenv)))
    except OSError:
        return []
    return sorted(n for n in names if any(fnmatch.fnmatchcase(n, pat) for pat in STRAY_BACKUP_PATTERNS))


def check_credential(cfg: Config) -> CheckResult:
    """Existence + permission bits + sibling file NAMES only — no file's contents are ever opened or
    read, and nothing beyond the mode/existence facts and backup-file names below is reported."""
    if not cfg.pgenv:
        return CheckResult("credential", "block", "SUVARNA_PGENV is not set")
    try:
        mode = os.stat(cfg.pgenv).st_mode
    except OSError:
        return CheckResult("credential", "block", "credential file does not exist")
    if mode & 0o077:
        return CheckResult("credential", "warn",
                            f"credential file is group- or world-readable (mode {oct(mode & 0o777)})")
    stray = _stray_backups(cfg.pgenv)
    if stray:
        return CheckResult("credential", "warn",
                            f"credential backup file(s) beside the credential ({', '.join(stray[:5])}"
                            f"{', …' if len(stray) > 5 else ''}): move them to ~/.config/madhav-admin/")
    return CheckResult("credential", "ok", "credential file exists with restricted permissions")


_SECRET_TOKEN_RE = re.compile(r"postgres://|password|@", re.IGNORECASE)


def _sanitize_query_output(text: str) -> str:
    """Drop any whitespace-delimited token that could echo a connection string or secret
    (containing ``postgres://``, ``password``, or ``@``) before it ever reaches a detail string —
    query stderr can otherwise leak a DSN verbatim (Fix 3, review #16)."""
    if not text:
        return ""
    kept = [t for t in text.split() if not _SECRET_TOKEN_RE.search(t)]
    return " ".join(kept)[:200]


# D6 (native, 2026-09-29): Suvarṇa reads production as the dedicated login `suvarna_reader`, created by
# platform/scripts/suvarna-reader-bootstrap.ts. The check below is the continuous half of that
# bootstrap's verification block: every effective-privilege question a login can answer about itself.
READER_LOGIN = "suvarna_reader"

# Accepted SECURITY DEFINER exceptions, exactly as the bootstrap's `--accept-secdef` values (the
# `regprocedure` text, e.g. `public.f(integer)`), separated by ';' because signatures contain commas.
SECDEF_ALLOW_ENV = "SUVARNA_READER_SECDEF_ALLOW"

# The reader's role defaults, exactly as suvarna-reader-bootstrap.ts READER_ROLE_CONFIG sets them
# (pg_db_role_setting rows, `<setdatabase>:<name>=<value>`; 0 = all databases). temp_file_limit is
# not a role default: the instance-level Cloud SQL flag bounds it (review of 4b979ce52, M6).
ROLE_READ_ONLY_DEFAULT = "0:default_transaction_read_only=on"
EXPECTED_ROLE_CONFIG = frozenset({
    ROLE_READ_ONLY_DEFAULT, "0:statement_timeout=120s",
    "0:idle_in_transaction_session_timeout=60s", "0:lock_timeout=5s",
})

# Mirrors of suvarna-reader-bootstrap.ts (test_monitor pins them to the script's own lists).
DENY_PATTERNS = (
    "profiles", "access_requests", "conversation_%", "mcp_oauth_%", "ai_provider_connections",
    "mv_session_summary", "query_baseline_stats", "mcp_api_keys",
    "message_parts", "mcp_sessions", "planner_managed_prashna_jobs", "admin_audit_log", "audit_log",
    "audit_events", "ai_custom_configurations", "ai_user_defaults", "ai_cli_grants", "chart_subject_consent%",
    "messages", "documents", "reports", "chat_attachments", "message_feedback",
    "ai_configuration_audit_log", "ai_conversation_selections", "ai_custom_configuration_roles",
    "ai_turn_routing_snapshots", "llm_usage_events", "notification_views", "pending_streams", "personas",
    "projects", "query_trace_steps", "eval_runs",
)
CHARTS_GRANTED_COLUMNS = ("id", "chart_id", "role", "ayanamsa", "house_system", "created_at", "created_at_iso")
CHART_GRANTS_GRANTED_COLUMNS = ("chart_id", "principal_id")


def _sql_list(items) -> str:
    """A SQL text-array literal of plain identifiers/patterns (no quotes inside, asserted)."""
    for it in items:
        assert re.fullmatch(r"[a-z0-9_%]+", it), it
    return "array[" + ",".join(f"'{it}'" for it in items) + "]"


def _withheld_readable_sql(relname: str, granted) -> str:
    return (f"(select count(*) from pg_attribute a join pg_class c on c.oid = a.attrelid join pg_namespace n "
            f"on n.oid = c.relnamespace where n.nspname = 'public' and c.relname = '{relname}' and a.attnum > 0 "
            f"and not a.attisdropped and a.attname <> all ({_sql_list(granted)}::name[]) "
            f"and has_column_privilege(current_user, c.oid, a.attnum, 'SELECT'))::text")


def _table_select_sql(relname: str) -> str:
    return (f"coalesce((select has_table_privilege(current_user, c.oid, 'SELECT') from pg_class c join pg_namespace n "
            f"on n.oid = c.relnamespace where n.nspname = 'public' and c.relname = '{relname}'), false)::text")

# One psql round trip; one `key|value` row per fact, terminated by `end|ok` so a truncated result can
# never pass. Every privilege function is evaluated for `current_user` — the login itself. The SQL is
# shlex-quoted into bash (see _default_credential_query_fn); it is still kept free of `$`, `!`,
# backtick, backslash and double quote as a second layer (test_self_privilege_sql_is_shell_safe).
_REL_SCOPE = "not (n.nspname ~ '^pg_toast' or n.nspname ~ '^pg_temp_')"
_SELF_PRIVILEGE_SQL = " ".join(f"""
with me as (select oid from pg_roles where rolname = current_user),
rels as (select c.oid, c.relkind from pg_class c join pg_namespace n on n.oid = c.relnamespace where {_REL_SCOPE}
  and not (n.nspname = 'pg_catalog' and c.relname = 'pg_settings')),
facts(k, v) as (
  select 'current_user', current_user::text
  union all select 'session_user', session_user::text
  union all select 'read_only', current_setting('default_transaction_read_only')
  union all select 'read_only_source', coalesce((select source from pg_settings where name = 'default_transaction_read_only'), '?')
  union all select 'role_config', coalesce((select string_agg(s.setdatabase::text || ':' || c, ',' order by s.setdatabase, c)
                                              from pg_db_role_setting s join me on s.setrole = me.oid
                                              cross join lateral unnest(s.setconfig) c), '')
  union all select 'elevated', (select (rolsuper or rolcreaterole or rolcreatedb or rolreplication or rolbypassrls)::text
                                  from pg_roles where rolname = current_user)
  union all select 'table_write', count(*)::text from rels where relkind in ('r','p','v','m','f')
    and has_table_privilege(current_user, oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
  union all select 'column_write', count(*)::text from rels where relkind in ('r','p','v','m','f')
    and has_any_column_privilege(current_user, oid, 'INSERT,UPDATE,REFERENCES')
  union all select 'sequence_write', count(*)::text from rels where relkind = 'S'
    and case when relkind = 'S' then has_sequence_privilege(current_user, oid, 'USAGE,UPDATE') else false end
  union all select 'database_create', has_database_privilege(current_user, current_database(), 'CREATE')::text
  union all select 'database_temp', has_database_privilege(current_user, current_database(), 'TEMPORARY')::text
  union all select 'schema_create', count(*)::text from pg_namespace n where {_REL_SCOPE}
    and has_schema_privilege(current_user, n.oid, 'CREATE')
  union all select 'member_of', count(*)::text from pg_auth_members m join me on m.member = me.oid
  union all select 'members_of_me', count(*)::text from pg_auth_members m join me on m.roleid = me.oid
  union all select 'owned_objects', ((select count(*) from pg_shdepend d join me on d.refobjid = me.oid
                                       where d.refclassid = 'pg_authid'::regclass and d.deptype = 'o')
                                    + (select count(*) from pg_database d join me on d.datdba = me.oid))::text
  union all select 'charts_table_select', {_table_select_sql('charts')}
  union all select 'chart_grants_table_select', {_table_select_sql('chart_grants')}
  union all select 'charts_withheld_readable', {_withheld_readable_sql('charts', CHARTS_GRANTED_COLUMNS)}
  union all select 'chart_grants_withheld_readable', {_withheld_readable_sql('chart_grants', CHART_GRANTS_GRANTED_COLUMNS)}
  union all select 'denied_readable', (select count(*) from pg_class c join pg_namespace n on n.oid = c.relnamespace
      where c.relkind in ('r','p','v','m','f')
        and (n.nspname = 'auth' or (n.nspname in ('public','nirmana_evidence') and c.relname like any ({_sql_list(DENY_PATTERNS)})))
        and has_schema_privilege(current_user, n.oid, 'USAGE') and has_any_column_privilege(current_user, c.oid, 'SELECT'))::text
  union all select 'large_objects', (select count(*) from pg_largeobject_metadata l join me on l.lomowner = me.oid)::text
  union all select 'acl_outside_scope', (select count(*) from pg_shdepend d join me on d.refobjid = me.oid
      where d.refclassid = 'pg_authid'::regclass and d.deptype = 'a'
        and not (d.dbid = (select oid from pg_database where datname = current_database())
                 and d.classid in ('pg_class'::regclass, 'pg_namespace'::regclass))
        and not (d.dbid = 0 and d.classid = 'pg_database'::regclass))::text
  union all select 'auth_schema_usage', coalesce((select has_schema_privilege(current_user, oid, 'USAGE')
                                                    from pg_namespace where nspname = 'auth'), false)::text
  union all select 'auth_dependent_views', (
    with recursive dep(root, ref) as (
      select r.ev_class, d.refobjid from pg_rewrite r join pg_depend d on d.classid = 'pg_rewrite'::regclass
        and d.objid = r.oid and d.refclassid = 'pg_class'::regclass and d.refobjid <> r.ev_class
      union
      select dep.root, d.refobjid from dep join pg_rewrite r on r.ev_class = dep.ref join pg_depend d
        on d.classid = 'pg_rewrite'::regclass and d.objid = r.oid and d.refclassid = 'pg_class'::regclass
        and d.refobjid <> r.ev_class)
    select count(distinct dep.root)::text from dep
      join pg_class t on t.oid = dep.ref join pg_namespace tn on tn.oid = t.relnamespace
      join pg_class v on v.oid = dep.root join pg_namespace vn on vn.oid = v.relnamespace
     where tn.nspname = 'auth' and vn.nspname <> 'auth'
       and has_schema_privilege(current_user, vn.oid, 'USAGE') and has_any_column_privilege(current_user, v.oid, 'SELECT'))
  union all (select 'secdef', p.oid::regprocedure::text from pg_proc p join pg_namespace n on n.oid = p.pronamespace
              where p.prosecdef and n.nspname <> 'pg_catalog'
                and p.prorettype not in ('trigger'::regtype, 'event_trigger'::regtype)
                and has_function_privilege(current_user, p.oid, 'EXECUTE'))
  union all select 'end', 'ok'
)
select k || '|' || v from facts;
""".split())

_COUNT_KEYS = ("table_write", "column_write", "sequence_write", "schema_create", "member_of", "members_of_me",
               "owned_objects", "large_objects", "acl_outside_scope", "auth_dependent_views",
               "charts_withheld_readable", "chart_grants_withheld_readable", "denied_readable")
_BOOL_KEYS = ("elevated", "database_create", "database_temp", "auth_schema_usage",
              "charts_table_select", "chart_grants_table_select")
_REQUIRED_KEYS = ("current_user", "session_user", "read_only", "read_only_source", "role_config") + _COUNT_KEYS + _BOOL_KEYS


def _secdef_allowlist() -> frozenset[str]:
    raw = os.environ.get(SECDEF_ALLOW_ENV, "")
    return frozenset(s.strip() for s in raw.split(";") if s.strip())


def _parse_self_privileges(out: str) -> dict | str:
    """Parse the ``key|value`` rows. Returns the facts, or a string naming why they cannot be trusted
    (missing terminator, missing key, non-numeric count, non-boolean flag) — never a partial pass."""
    facts: dict = {"secdef": []}
    # A bare `SET` command tag (psql without -q) is the only non key|value line tolerated.
    lines = [ln.strip() for ln in (out or "").splitlines() if ln.strip() and ln.strip() != "SET"]
    if not lines or lines[-1] != "end|ok":
        return "self-privilege query output incomplete (no end marker)"
    for ln in lines[:-1]:
        key, sep, value = ln.partition("|")
        if not sep:
            return "self-privilege query returned an unparseable row"
        if key == "secdef":
            facts["secdef"].append(value)
        else:
            facts[key] = value
    missing = [k for k in _REQUIRED_KEYS if k not in facts]
    if missing:
        return f"self-privilege query missing facts: {', '.join(missing)}"
    for k in _COUNT_KEYS:
        try:
            facts[k] = int(facts[k])
        except ValueError:
            return f"self-privilege fact {k} is not a count"
    for k in _BOOL_KEYS:
        if facts[k] not in ("true", "false"):
            return f"self-privilege fact {k} is not a boolean"
        facts[k] = facts[k] == "true"
    return facts


def check_credential_readonly(cfg: Config) -> CheckResult:
    """Verify, as the credential's own login, that it has no write path at all — not only that its
    file permissions look right and not only that the session flag is on. One query (run through the
    injectable query function, which sources the file inside a subprocess shell; this process never
    opens it) evaluates for ``current_user``: table and column write privileges on every relation,
    sequence USAGE/UPDATE, database and schema CREATE, role memberships in both directions, owned
    objects and owned large objects, ACL dependencies outside this database's relations/schemas and
    CONNECT (pg_shdepend catch-all), elevated role attributes, executable SECURITY DEFINER functions
    outside pg_catalog in ANY schema (operators, casts and aggregates can reach them without schema
    USAGE; trigger/event-trigger functions excluded), whether schema ``auth`` (or any readable view
    over it) is reachable, table-level SELECT on public.charts / public.chart_grants, readable
    withheld columns of either, and readable deny-listed relations — every one of those is ``block``.
    A missing role default default_transaction_read_only=on is also ``block``; other role-default
    drift is ``warn``.

    ``block`` on any write path; ``ok`` only if every check passes AND session_user = current_user =
    ``suvarna_reader`` AND the session's default_transaction_read_only is on AND the role's own
    defaults (pg_db_role_setting) equal EXPECTED_ROLE_CONFIG; the session value (PGOPTIONS or role
    default, with its pg_settings source) and the role default are reported separately. ``warn``
    with the detail otherwise, when another role can assume this one, or when the query cannot run /
    returns output that cannot be trusted. Never fabricates a pass (CLAUDE.md §N.8)."""
    name = "credential_readonly"
    if not cfg.pgenv:
        return CheckResult(name, "warn", "SUVARNA_PGENV is not set; cannot verify read-only access")
    if not os.path.exists(cfg.pgenv):
        return CheckResult(name, "warn", "credential file does not exist; cannot verify read-only access")
    try:
        rc, out, err = cfg.credential_query_fn(cfg.pgenv, _SELF_PRIVILEGE_SQL, 20)
    except Exception as exc:  # noqa: BLE001
        return CheckResult(name, "warn",
                            f"self-privilege query failed: {type(exc).__name__}: {_sanitize_query_output(str(exc))}")
    if rc != 0:
        return CheckResult(name, "warn", f"cannot run self-privilege check ({_sanitize_query_output(err or out)})")
    facts = _parse_self_privileges(out)
    if isinstance(facts, str):
        return CheckResult(name, "warn", facts)

    login = _sanitize_query_output(str(facts["current_user"])) or "?"
    allowed = cfg.secdef_allowlist if cfg.secdef_allowlist is not None else _secdef_allowlist()
    secdef = [s for s in facts["secdef"] if s not in allowed]
    write_paths = []
    if facts["elevated"]:
        write_paths.append("elevated role attributes")
    for key, label in (("table_write", "relations with INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER"),
                       ("column_write", "relations with column INSERT/UPDATE/REFERENCES"),
                       ("sequence_write", "sequences with USAGE/UPDATE"),
                       ("schema_create", "schemas with CREATE"),
                       ("member_of", "role memberships"),
                       ("owned_objects", "owned objects"),
                       ("large_objects", "owned large objects"),
                       ("acl_outside_scope", "ACL grants outside this database's relations/schemas/CONNECT"),
                       ("charts_withheld_readable", "withheld public.charts columns readable"),
                       ("chart_grants_withheld_readable", "withheld public.chart_grants columns readable"),
                       ("denied_readable", "deny-listed or auth relations readable"),
                       ("auth_dependent_views", "readable views over schema auth")):
        if facts[key]:
            write_paths.append(f"{label}={facts[key]}")
    if facts["database_create"]:
        write_paths.append("database CREATE")
    if facts["auth_schema_usage"]:
        write_paths.append("USAGE on schema auth")
    if facts["charts_table_select"]:
        write_paths.append("table-level SELECT on public.charts (withheld birth data readable)")
    if facts["chart_grants_table_select"]:
        write_paths.append("table-level SELECT on public.chart_grants")
    if secdef:
        shown = _sanitize_query_output(", ".join(secdef[:3]))
        write_paths.append(f"reachable SECURITY DEFINER functions={len(secdef)} ({shown}{', …' if len(secdef) > 3 else ''})")
    if write_paths:
        return CheckResult(name, "block", f"login {login} has a write path or exposure: " + "; ".join(write_paths))

    # L6: the role's own read-only default is the one setting whose absence is a BLOCK — a session
    # that forgets PGOPTIONS would otherwise start read-write (other role-default drift stays WARN).
    role_config = frozenset(e for e in str(facts["role_config"]).split(",") if e)
    if ROLE_READ_ONLY_DEFAULT not in role_config:
        return CheckResult(name, "block", f"login {login}: role default default_transaction_read_only is not on "
                                          f"(ALTER ROLE {READER_LOGIN} SET default_transaction_read_only = on)")

    session = _sanitize_query_output(str(facts["session_user"])) or "?"
    ro_flag = _sanitize_query_output(str(facts["read_only"])).lower() or "?"
    ro_source = _sanitize_query_output(str(facts["read_only_source"])) or "?"
    role_ro = "on"
    temp = "temp tables allowed (session-local)" if facts["database_temp"] else "no temp"
    accepted = f", {len(facts['secdef'])} accepted security-definer exception(s)" if facts["secdef"] else ""
    concerns = []
    if login != READER_LOGIN or session != login:
        concerns.append(f"session_user={session} current_user={login}, expected both {READER_LOGIN}")
    if facts["members_of_me"]:
        concerns.append(f"{facts['members_of_me']} other role(s) can assume this login")
    if ro_flag != "on":
        concerns.append(f"session default_transaction_read_only={ro_flag} (source {ro_source})")
    if role_config != EXPECTED_ROLE_CONFIG:
        missing = sorted(EXPECTED_ROLE_CONFIG - role_config)
        extra = sorted(role_config - EXPECTED_ROLE_CONFIG)
        concerns.append("role defaults differ from the expected set"
                        + (f"; missing {_sanitize_query_output(', '.join(missing))}" if missing else "")
                        + (f"; unexpected {_sanitize_query_output(', '.join(extra))}" if extra else ""))
    if concerns:
        return CheckResult(name, "warn", "no write path found, but " + "; ".join(concerns))
    return CheckResult(name, "ok", f"{READER_LOGIN}: no write path (tables, columns, sequences, create, memberships, "
                                   f"ownership, large objects, out-of-scope ACLs, security-definer, auth all clear"
                                   f"{accepted}); session default_transaction_read_only=on (source {ro_source}); "
                                   f"role default read-only={role_ro}, role defaults as expected; {temp}")


_BATTERY_PCT_RE = re.compile(r"(\d+)%")


def check_power(cfg: Config) -> CheckResult:
    src = cfg.power_source_fn()
    if src == "ac":
        return CheckResult("power", "ok", "on AC power")
    if src.startswith("battery"):
        m = _BATTERY_PCT_RE.search(src)
        if not m:
            return CheckResult("power", "warn", f"on battery, level unknown ({src})")
        pct = int(m.group(1))
        if pct < 50:
            return CheckResult("power", "block", f"on battery at {pct}% (below 50%)")
        return CheckResult("power", "warn", f"on battery at {pct}%")
    return CheckResult("power", "warn", f"power source unknown ({src})")


_ASSERTION_RE = re.compile(r"(PreventUserIdleSystemSleep|PreventSystemSleep)\s+(\d+)")


def check_sleep_prevented(cfg: Config) -> CheckResult:
    rc, out = cfg.run_fn(["pgrep", "-x", "caffeinate"], timeout=5)
    if rc == 0 and out.strip():
        return CheckResult("sleep_prevented", "ok", "caffeinate is running")
    rc2, out2 = cfg.run_fn(["pmset", "-g", "assertions"], timeout=5)
    if rc2 == 0 and any(v == "1" for _, v in _ASSERTION_RE.findall(out2)):
        return CheckResult("sleep_prevented", "ok", "a sleep-prevention assertion is active")
    return CheckResult("sleep_prevented", "warn", "sleep is not prevented (no caffeinate, no active assertion)")


def check_hold(cfg: Config) -> CheckResult:
    if os.path.exists(cfg.hold_path):
        return CheckResult("hold", "block", "hold switch on: dispatch nothing new")
    return CheckResult("hold", "ok", "hold switch off")


def check_disk(cfg: Config) -> CheckResult:
    free_gb = cfg.disk_free_fn(cfg.home) / (1024 ** 3)
    if free_gb < 5:
        return CheckResult("disk", "block", f"{free_gb:.1f} GB free (below 5 GB)")
    if free_gb < 20:
        return CheckResult("disk", "warn", f"{free_gb:.1f} GB free (below 20 GB)")
    return CheckResult("disk", "ok", f"{free_gb:.1f} GB free")


def check_tracker(cfg: Config) -> CheckResult:
    url = f"http://{cfg.tracker_host}:{cfg.tracker_port}/api/health"
    status, body, err = cfg.http_get_fn(url, 3.0)
    if err or status is None:
        return CheckResult("tracker", "warn", f"tracker unreachable ({err or 'no response'})")
    try:
        data = json.loads(body) if body else {}
    except ValueError:
        data = {}
    if status == 200 and data.get("ok") is True:
        return CheckResult("tracker", "ok", "tracker healthy")
    return CheckResult("tracker", "warn", f"tracker unhealthy (status {status}, ok={data.get('ok')})")


def _latest_conductor_heartbeat_ts(events_path: str) -> str | None:
    """The ``ts`` of the newest ``kind: heartbeat, actor: conductor`` line in the event log, or
    ``None`` if none has ever been written. Tolerant of a missing file and of malformed lines
    (skipped, never fatal) — mirrors events.EventLog's own tolerance, but a single forward scan is
    enough here since this check only ever needs the single newest timestamp."""
    latest: str | None = None
    try:
        with open(events_path, encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(ev, dict):
                    continue
                if ev.get("kind") == "heartbeat" and ev.get("actor") == "conductor":
                    ts = ev.get("ts")
                    if isinstance(ts, str) and (latest is None or ts > latest):
                        latest = ts
    except FileNotFoundError:
        pass
    return latest


def check_conductor_heartbeat(cfg: Config) -> CheckResult:
    """L.15: is either interim runtime session's Conductor still emitting its per-pass heartbeat
    (arch §5.1)? ``ok`` with "no conductor yet" before the swarm has ever run — that is a fact about
    campaign phase, not an environment failure, so it must never read as a problem. Otherwise ``warn``
    once the newest heartbeat is older than ``conductor_stale_min`` (default 45) minutes; never
    ``block`` — a stale Conductor is the watchdog's job (arch §5.5, charter G15), not a dispatch
    gate, and this check only needs to make the staleness visible on the dashboard and in a
    notification (--notify)."""
    name = "conductor_heartbeat"
    ts = _latest_conductor_heartbeat_ts(cfg.events_path)
    if ts is None:
        return CheckResult(name, "ok", "no conductor yet")
    try:
        seen = dt.datetime.fromisoformat(ts)
    except ValueError:
        return CheckResult(name, "warn", f"latest conductor heartbeat has an unparseable timestamp ({ts!r})")
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=dt.timezone.utc)
    now = cfg.now_fn() if cfg.now_fn else dt.datetime.now(dt.timezone.utc)
    age_min = (now - seen).total_seconds() / 60.0
    if age_min > cfg.conductor_stale_min:
        return CheckResult(name, "warn",
                            f"latest conductor heartbeat is {age_min:.0f} min old (over {cfg.conductor_stale_min})")
    return CheckResult(name, "ok", f"latest conductor heartbeat is {age_min:.0f} min old")


def check_isolation(cfg: Config) -> CheckResult:
    """CODE-12 (S1, L.16a, arch §2.4): the isolation gate — a separate macOS user (N-25), unreadable
    credential/admin paths, a decisions log the swarm cannot write, and settings-file hashes matched
    against a native-recorded baseline. **N-25 is not yet implemented**: there is no separate user,
    no recorded baseline, nothing to compare. Until it lands this check can only ever ``warn`` — it
    must never fabricate ``ok`` (nothing exists yet to verify) and must never ``block`` (that would
    make today's single-user environment permanently undispatchable for a gate it cannot yet satisfy;
    CLAUDE.md §N.8 — a signal without the check it claims is null, not green, but here it is also not
    a reason to stop). The expected user is configurable (`Config.isolation_expected_user`, else
    ``SUVARNA_ISOLATION_EXPECTED_USER``, else the current user) so the check's shape — and its
    detail — is ready the day N-25 actually stands up the separate account."""
    current_user = cfg.getuser_fn() if cfg.getuser_fn else getpass.getuser()
    expected_user = cfg.isolation_expected_user or os.environ.get(ISOLATION_EXPECTED_USER_ENV) or current_user
    return CheckResult("isolation", "warn",
                       f"N-25 not implemented: swarm runs as the native's user ({current_user!r}); "
                       f"expected user under N-25: {expected_user!r}")


def check_decision_writers(cfg: Config) -> CheckResult:
    """CODE-13 (S2): any `decided` line in the decisions log whose `writer` is not
    `strategic-suvarna` blocks — the log is the one place a native ruling is recorded, and a line
    written by anyone else is exactly the forgery N-25/P14 exist to prevent."""
    log = load_decisions(cfg.decisions_path)
    bad = sorted(rec_id for rec_id, rec in log["latest"].items()
                if rec.get("state") == "decided" and rec.get("writer") != DECISIONS_ALLOWED_WRITER)
    if bad:
        return CheckResult("decision_writers", "block",
                           f"decided line(s) not written by {DECISIONS_ALLOWED_WRITER}: {', '.join(bad)}")
    n = len(log["latest"])
    return CheckResult("decision_writers", "ok",
                       f"all {n} decision(s) in the log written by {DECISIONS_ALLOWED_WRITER}" if n
                       else "no decisions recorded yet")


def _normalize_builder_grants(grants) -> list[tuple[str | None, str | None]]:
    out: list[tuple[str | None, str | None]] = []
    for g in grants or []:
        if isinstance(g, dict):
            out.append((g.get("chart_id"), g.get("permission")))
        elif isinstance(g, (list, tuple)) and len(g) == 2:
            out.append((g[0], g[1]))
    return sorted(out)


def check_builder_scope(cfg: Config) -> CheckResult:
    """CODE-15 (C3, Track E brief §8 E7.3): the builder's own scope, measured through the
    authenticated `suvarna-build --preflight` (the reader cannot read `chart_grants.permission` or
    `profiles`, D6 — never a live database read). Absent before provisioning (E7.2) reads `ok`, "no
    builder identity recorded yet" — a fact about campaign phase, the same convention
    `conductor_heartbeat` uses before the swarm has ever run. Once `run/builder_identity.json`
    exists, anything short of an exact match — role `guest`, status `active`, grants exactly
    `[(BUILDER_CHART_ID, 'build')]`, and equal to the recorded identity — blocks; so does a missing
    script or a failed preflight."""
    name = "builder_scope"
    if not os.path.exists(cfg.builder_identity_path):
        return CheckResult(name, "ok", "no builder identity recorded yet (E7.2 not done)")
    try:
        with open(cfg.builder_identity_path, encoding="utf-8") as f:
            identity = json.load(f)
    except (OSError, ValueError) as exc:
        return CheckResult(name, "block", f"builder_identity.json unreadable: {type(exc).__name__}: {exc}"[:200])
    if not isinstance(identity, dict):
        return CheckResult(name, "block", "builder_identity.json does not contain a JSON object")
    try:
        rc, out = cfg.run_fn([cfg.suvarna_build_cmd, "--preflight"], timeout=15)
    except OSError as exc:  # the script itself is missing — CODE-15: blocks once identity exists
        return CheckResult(name, "block", f"suvarna-build not found ({cfg.suvarna_build_cmd}): {exc}"[:200])
    if rc != 0:
        return CheckResult(name, "block", f"suvarna-build --preflight failed: {out.strip()[:200]}")
    try:
        pre = json.loads(out)
    except ValueError:
        return CheckResult(name, "block", f"suvarna-build --preflight: non-JSON output: {out.strip()[:160]}")
    builder = pre.get("builder")
    if not isinstance(builder, dict):
        return CheckResult(name, "block", "preflight reported no builder scope")
    id_builder = identity.get("builder", identity)
    problems = []
    if builder.get("role") != "guest":
        problems.append(f"role={builder.get('role')!r} (expected 'guest')")
    if builder.get("status") != "active":
        problems.append(f"status={builder.get('status')!r} (expected 'active')")
    grants = _normalize_builder_grants(builder.get("grants"))
    expected_grants = [(BUILDER_CHART_ID, "build")]
    if grants != expected_grants:
        problems.append(f"grants={grants} (expected {expected_grants})")
    if (builder.get("principal_id") != id_builder.get("principal_id")
            or builder.get("role") != id_builder.get("role")
            or builder.get("status") != id_builder.get("status")
            or grants != _normalize_builder_grants(id_builder.get("grants"))):
        problems.append("preflight builder scope does not match run/builder_identity.json")
    if problems:
        return CheckResult(name, "block", "; ".join(problems))
    return CheckResult(name, "ok", f"builder {builder.get('principal_id')}: role=guest status=active "
                                   f"grants={grants}, matches builder_identity.json")


_CHECK_FNS: dict[str, Callable[[Config], CheckResult]] = {
    "db_proxy": check_db_proxy,
    "credential": check_credential,
    "credential_readonly": check_credential_readonly,
    "power": check_power,
    "sleep_prevented": check_sleep_prevented,
    "hold": check_hold,
    "disk": check_disk,
    "tracker": check_tracker,
    "conductor_heartbeat": check_conductor_heartbeat,
    "isolation": check_isolation,
    "decision_writers": check_decision_writers,
    "builder_scope": check_builder_scope,
}


def _safe_check(name: str, cfg: Config) -> CheckResult:
    try:
        return _CHECK_FNS[name](cfg)
    except Exception as exc:  # noqa: BLE001 — a broken check is a warn, never a crash (CLAUDE.md §N.8)
        return CheckResult(name, "warn", f"{name} check raised {type(exc).__name__}: {exc}"[:300])


def run_checks(cfg: Config) -> list[CheckResult]:
    return [_safe_check(name, cfg) for name in CHECK_NAMES]


def overall_status(results: list[CheckResult]) -> str:
    if not results:
        return "ok"
    return max(results, key=lambda r: STATUS_RANK.get(r.status, 1)).status


def exit_code(status: str) -> int:
    return {"ok": 0, "warn": 1, "block": 2}.get(status, 1)


# --------------------------------------------------------------------------------------------
# Repair (conservative: only starts a process verifiably not already running; never touches
# hold / credential / disk / power)
# --------------------------------------------------------------------------------------------

def _repair_tracker(cfg: Config) -> list[str]:
    if os.path.exists(cfg.tracker_stop_path):
        return []  # operator asked the supervisor to stay down — do not second-guess it
    rc, out = cfg.run_fn(["pgrep", "-f", "run_tracker.sh"], timeout=5)
    if rc == 0 and out.strip():
        return ["tracker: run_tracker.sh already running, not restarting"]
    script = os.path.join(cfg.package_dir, "run_tracker.sh")
    try:
        cfg.launch_fn(["bash", script], cwd=cfg.package_dir, log_path=None, env=dict(os.environ))
        return [f"tracker: started {os.path.basename(script)} detached"]
    except Exception as exc:  # noqa: BLE001
        return [f"tracker: repair failed: {type(exc).__name__}: {exc}"]


def _repair_db_proxy(cfg: Config) -> list[str]:
    # Match a proxy on OUR port only: other workstreams run their own proxies on other ports
    # (the Gochara lane uses 55440), and one of those must not stop this repair.
    rc, out = cfg.run_fn(["pgrep", "-f", f"cloud-sql-proxy.*--port[ =]{cfg.db_port}( |$)"], timeout=5)
    if rc == 0 and out.strip():
        return [f"db_proxy: a cloud-sql-proxy for port {cfg.db_port} is already running (starting up?), not starting another"]
    log_path = os.path.join(cfg.run_dir, "proxy.log")
    argv = ["cloud-sql-proxy", "--address", "127.0.0.1", "--port", str(cfg.db_port),
            "madhav-astrology:asia-south1:amjis-postgres"]
    try:
        os.makedirs(cfg.run_dir, exist_ok=True)
        cfg.launch_fn(argv, cwd=None, log_path=log_path, env=None)
        return [f"db_proxy: started cloud-sql-proxy on port {cfg.db_port} detached"]
    except Exception as exc:  # noqa: BLE001
        return [f"db_proxy: repair failed: {type(exc).__name__}: {exc}"]


def _repair_sleep(cfg: Config) -> list[str]:
    rc, out = cfg.run_fn(["pgrep", "-x", "caffeinate"], timeout=5)
    if rc == 0 and out.strip():
        return ["sleep_prevented: caffeinate already running"]
    try:
        cfg.launch_fn(["caffeinate", "-dimsu"], cwd=None, log_path=None, env=None)
        return ["sleep_prevented: started caffeinate -dimsu detached"]
    except Exception as exc:  # noqa: BLE001
        return [f"sleep_prevented: repair failed: {type(exc).__name__}: {exc}"]


def repair(cfg: Config, by_name: dict[str, CheckResult]) -> list[str]:
    """Attempt to fix the checks that can be fixed unattended. The hold switch, when on, suppresses
    every repair action (dispatch nothing new means nothing new — including a repair launch)."""
    if os.path.exists(cfg.hold_path):
        return []
    actions: list[str] = []
    tracker = by_name.get("tracker")
    if tracker is not None and tracker.status != "ok":
        actions += _repair_tracker(cfg)
    db_proxy = by_name.get("db_proxy")
    if db_proxy is not None and db_proxy.status != "ok":
        actions += _repair_db_proxy(cfg)
    sleep = by_name.get("sleep_prevented")
    if sleep is not None and sleep.status != "ok":
        actions += _repair_sleep(cfg)
    return actions


# --------------------------------------------------------------------------------------------
# --emit: heartbeat every run, a note only when the non-ok set changes
# --------------------------------------------------------------------------------------------

_SHORT = {
    ("db_proxy", "block"): "down", ("db_proxy", "warn"): "degraded",
    ("credential", "block"): "missing/insecure", ("credential", "warn"): "too open",
    ("power", "block"): "critical", ("power", "warn"): "battery",
    ("sleep_prevented", "warn"): "not prevented",
    ("hold", "block"): "on",
    ("disk", "block"): "critical", ("disk", "warn"): "low",
    ("tracker", "warn"): "unreachable",
    ("conductor_heartbeat", "warn"): "stale",
}


def _summary_line(overall: str, results: list[CheckResult]) -> str:
    if overall == "ok":
        return f"ok: {len(results)}/{len(results)}"
    non_ok = [r for r in results if r.status != "ok"]
    parts = [f"{r.name} {_SHORT.get((r.name, r.status), r.status)}" for r in non_ok]
    prefix = "BLOCK" if overall == "block" else "WARN"
    return f"{prefix}: " + "; ".join(parts)


def _load_state(cfg: Config) -> dict:
    try:
        with open(cfg.state_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_state(cfg: Config, state: dict) -> None:
    os.makedirs(cfg.run_dir, exist_ok=True)
    tmp = f"{cfg.state_path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, cfg.state_path)  # atomic


def _non_ok_names(results: list[CheckResult]) -> list[str]:
    return sorted(r.name for r in results if r.status != "ok")


def emit(cfg: Config, results: list[CheckResult], overall: str, repairs: list[str],
         changed: bool | None = None) -> list[str]:
    """Append a heartbeat every call, plus a note when the non-ok set changed since the last run
    (dedupe via monitor_state.json) and one note per repair action taken. Never raises — every
    failure is caught and returned as a string in the result.

    ``changed``, when given, is used instead of re-deriving it from state: ``run_once`` computes it
    once so ``--emit`` and ``--notify`` agree on the same answer and the state is saved exactly once
    per run. ``None`` (the default; every direct caller before --notify existed) recomputes it here,
    unchanged from the original behaviour."""
    errors: list[str] = []
    summary = _summary_line(overall, results)

    def _append(ev: dict, what: str) -> None:
        try:
            append(cfg.events_path, ev)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{what} emit failed: {type(exc).__name__}: {exc}")

    _append({"kind": "heartbeat", "actor": "monitor", "detail": summary}, "heartbeat")

    non_ok = _non_ok_names(results)
    if changed is None:
        prev = _load_state(cfg)
        changed = prev.get("non_ok") != non_ok
    if changed:
        _append({"kind": "note", "actor": "monitor", "detail": summary}, "note")

    for action in repairs:
        _append({"kind": "note", "actor": "monitor", "detail": f"repair: {action}"}, "repair note")

    try:
        _save_state(cfg, {"non_ok": non_ok, "at": now_iso()})
    except Exception as exc:  # noqa: BLE001
        errors.append(f"state save failed: {type(exc).__name__}: {exc}")
    return errors


def notify_on_change(cfg: Config, results: list[CheckResult], overall: str, changed: bool) -> None:
    """Fire exactly one macOS notification per state change (the same ``changed`` --emit computes),
    via ``cfg.notify_fn`` (real default: ``osascript``). Never raises."""
    if not changed:
        return
    try:
        cfg.notify_fn(_summary_line(overall, results))
    except Exception:  # noqa: BLE001 — a failed notification must never fail the monitor
        pass


# --------------------------------------------------------------------------------------------
# One run, printing, CLI
# --------------------------------------------------------------------------------------------

def run_once(cfg: Config, emit_flag: bool = False, repair_flag: bool = False, notify_flag: bool = False) -> dict:
    results = run_checks(cfg)
    by_name = {r.name: r for r in results}
    repairs = repair(cfg, by_name) if repair_flag else []
    overall = overall_status(results)

    # Computed once so --emit and --notify agree on the same "did the non-ok set change" answer
    # and monitor_state.json is saved exactly once per run, whichever flags are active.
    changed = None
    if emit_flag or notify_flag:
        non_ok = _non_ok_names(results)
        changed = _load_state(cfg).get("non_ok") != non_ok

    emit_errors: list[str] = []
    if emit_flag:
        emit_errors = emit(cfg, results, overall, repairs, changed=changed)
    elif notify_flag:
        # --notify alone still needs the state saved, so its own dedupe persists across runs.
        try:
            _save_state(cfg, {"non_ok": _non_ok_names(results), "at": now_iso()})
        except Exception as exc:  # noqa: BLE001
            emit_errors.append(f"state save failed: {type(exc).__name__}: {exc}")

    notified = False
    if notify_flag and changed:
        notify_on_change(cfg, results, overall, changed)
        notified = True

    return {
        "generated_at": now_iso(),
        "overall": overall,
        "checks": [r.to_dict() for r in results],
        "repairs": repairs,
        "emit_errors": emit_errors,
        "notified": notified,
    }


def _print_human(report: dict) -> None:
    for c in report["checks"]:
        print(f"{c['status'].upper():5} {c['name']:16} {c['detail']}")
    print(f"overall: {report['overall'].upper()}")
    if report["repairs"]:
        print("repairs:")
        for r in report["repairs"]:
            print(f"  - {r}")
    if report["emit_errors"]:
        print("emit errors:")
        for e in report["emit_errors"]:
            print(f"  - {e}")


def _print(report: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        _print_human(report)


def watch(cfg: Config, seconds: int, emit_flag: bool, repair_flag: bool, as_json: bool,
          notify_flag: bool = False) -> None:
    interval = max(15, seconds)
    stop_event = threading.Event()

    def _on_term(signum, frame) -> None:  # noqa: ANN001
        stop_event.set()

    prev_handler = signal.signal(signal.SIGTERM, _on_term)
    try:
        while not stop_event.is_set():
            report = run_once(cfg, emit_flag=emit_flag, repair_flag=repair_flag, notify_flag=notify_flag)
            _print(report, as_json)
            stop_event.wait(interval)
    except KeyboardInterrupt:
        pass
    finally:
        signal.signal(signal.SIGTERM, prev_handler)


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suvarṇa Monitor — environment checker for the autonomous campaign")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true", help="run the checks once and exit (default)")
    mode.add_argument("--watch", type=int, metavar="SECONDS", help="loop, re-checking every SECONDS (minimum 15)")
    ap.add_argument("--emit", action="store_true", help="append a heartbeat (and note on change) to the event log")
    ap.add_argument("--repair", action="store_true", help="conservatively try to fix what can be fixed unattended")
    ap.add_argument("--notify", action="store_true",
                    help="send a macOS notification (osascript) on a change of the non-ok set "
                         "(shares --emit's dedupe state)")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    cfg = default_config()
    if args.watch:
        watch(cfg, args.watch, args.emit, args.repair, args.json, notify_flag=args.notify)
        return 0
    report = run_once(cfg, emit_flag=args.emit, repair_flag=args.repair, notify_flag=args.notify)
    _print(report, args.json)
    return exit_code(report["overall"])


if __name__ == "__main__":
    raise SystemExit(main())
