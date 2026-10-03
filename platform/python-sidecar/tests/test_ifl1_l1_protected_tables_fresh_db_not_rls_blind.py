"""I.FL1 tests-first, HELD until PR #2984 merges: I-23(c) / incident INCIDENT_CHART_DIVISIONALS F2 --
a database built from the migrations must not recreate the `chart_divisionals` access incident.

The incident (2026-09-18 to 2026-10-01): `002_ganita_divisionals.sql:62` enables row-level security on
`chart_divisionals` and creates ONE policy, `TO service_role` -- a role that does not exist on the
instance. Once migration 1035 moved the table to the NOLOGIN owner `data_plane_l1_owner`, no login
role could read a single row, and every reader (7 direct / 61 transitive dependents) was blind. Production
was repaired out of band (RLS disabled, plan D, 2026-10-01: SS decision record A-2 in the L1 decision
sheet); NO migration in this repository disables it. A fresh database built from the migration
files would therefore reproduce the incident.

What this test pins (the "cutover-gate check" part of decision Q-L1-01 / Track I item I-23):
for every protected L1 table the data-plane scripts name (`L1_ACTIVE_TABLES` in
`platform/scripts/data-plane-ownership-preflight.ts`, read from that file so the list cannot
drift), the migrations, taken together, must NOT leave row-level security enabled with no
usable policy. "Usable" means a policy with no `TO` clause (PUBLIC) or one naming some role other
than `service_role`. The fix is a guarded schema-of-record migration (idempotent, a no-op when the
caller is not the owner, never editing 002 or 1035), or any change that makes a fresh database
readable; the choice of fix is SS's (incident REVIEW Part III, "a decision for SS"). The live
database-side gate (a DB-backed check in `data-plane-ownership-status.ts`) is the incident
REVIEW's F2 and is a separate, TypeScript, DB-backed piece; this test is the static, DB-free
fresh-database counterpart.

Method and its honest limits: a textual replay over `platform/migrations/*.sql` and
`platform/supabase/migrations/*.sql` (SQL comments stripped inside the detector) of three statement shapes --
`ALTER TABLE <t> ENABLE|DISABLE ROW LEVEL SECURITY` and `CREATE POLICY ... ON <t> ... [TO roles]`.
It does not order the files and does not see dynamically built SQL (`format(...)` with %I); a
table is judged on the SET of events. A later DISABLE or a usable policy anywhere clears it.

Held with `xfail(strict=True)`: green now; when the schema-of-record fix lands this case XPASSes and
strict mode fails the build, which is the cue to remove the mark. `pytest --runxfail` shows the real
failure text on today's code.
"""
from __future__ import annotations

import pathlib
import re

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_PLATFORM = _SIDECAR.parent
_PREFLIGHT_TS = _PLATFORM / "scripts" / "data-plane-ownership-preflight.ts"
_MIGRATION_DIRS = (_PLATFORM / "migrations", _PLATFORM / "supabase" / "migrations")

#: a role name that is known not to exist on the instance: a policy only for it protects nothing
_NONEXISTENT_ROLES = frozenset({"service_role"})


def _l1_active_tables() -> list[str]:
    text = _PREFLIGHT_TS.read_text(encoding="utf-8")
    block = re.search(r"export const L1_ACTIVE_TABLES\s*=\s*\[(.*?)\]\s*as const", text, re.DOTALL)
    assert block, "L1_ACTIVE_TABLES not found in data-plane-ownership-preflight.ts (parse drift)"
    tables = re.findall(r"'([a-z0-9_]+)'", block.group(1))
    assert "chart_divisionals" in tables and len(tables) >= 10, tables
    return tables


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", " ", sql)


def _migration_texts() -> dict[str, str]:
    out: dict[str, str] = {}
    for d in _MIGRATION_DIRS:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.sql")):
            out[p.relative_to(_PLATFORM).as_posix()] = p.read_text(encoding="utf-8")
    return out


def _ident(table: str) -> str:
    return rf'(?:public\s*\.\s*)?"?{re.escape(table)}"?'


def rls_blind_tables(tables: list[str], texts: dict[str, str]) -> dict[str, list[str]]:
    """table -> evidence lines, for every table whose migrations enable RLS and never disable it or
    add a usable policy."""
    blind: dict[str, list[str]] = {}
    for t in tables:
        enabled_in: list[str] = []
        cleared = False
        policies: list[str] = []
        for fname, raw in texts.items():
            sql = _strip_sql_comments(raw)
            if re.search(rf"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:IF\s+EXISTS\s+)?{_ident(t)}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY", sql, re.I):
                enabled_in.append(fname)
            if re.search(rf"ALTER\s+TABLE\s+(?:ONLY\s+)?(?:IF\s+EXISTS\s+)?{_ident(t)}\s+DISABLE\s+ROW\s+LEVEL\s+SECURITY", sql, re.I):
                cleared = True
            for m in re.finditer(rf"CREATE\s+POLICY\s+(?:\"[^\"]+\"|\S+)\s+ON\s+{_ident(t)}\b(.{{0,400}})", sql, re.I | re.S):
                tail = m.group(1)
                role_m = re.search(
                    r"\bTO\s+((?:\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_]*)(?:\s*,\s*(?:\"[^\"]+\"|[A-Za-z_][A-Za-z0-9_]*))*)",
                    tail.split(";")[0], re.I)
                if role_m is None:
                    cleared = True   # no TO clause = PUBLIC
                    continue
                roles = {r.strip().strip('"').lower() for r in role_m.group(1).split(",") if r.strip()}
                if roles - _NONEXISTENT_ROLES:
                    cleared = True
                else:
                    policies.append(f"{fname}: policy only TO {sorted(roles)}")
        if enabled_in and not cleared:
            blind[t] = [f"RLS enabled in {', '.join(enabled_in)}", *policies] or ["RLS enabled"]
    return blind


# -- the detector must catch what it claims to (mutation proof; runs always) -----------------------------


def test_detector_flags_rls_on_with_only_a_nonexistent_role_policy_and_clears_the_fixes():
    base = {
        "m/002.sql": (
            "ALTER TABLE public.t1 ENABLE ROW LEVEL SECURITY;\n"
            "CREATE POLICY \"service role full access\" ON public.t1 AS PERMISSIVE FOR ALL TO service_role USING (true);\n"
            "-- ALTER TABLE public.t2 ENABLE ROW LEVEL SECURITY;  (a comment, not a statement)\n"
        )
    }
    assert set(rls_blind_tables(["t1", "t2"], base)) == {"t1"}
    assert rls_blind_tables(["t1"], {**base, "m/9.sql": "ALTER TABLE public.t1 DISABLE ROW LEVEL SECURITY;"}) == {}
    assert rls_blind_tables(
        ["t1"], {**base, "m/9.sql": "CREATE POLICY p ON public.t1 FOR SELECT TO data_plane_builder USING (true);"}
    ) == {}
    assert rls_blind_tables(["t1"], {**base, "m/9.sql": "CREATE POLICY p ON public.t1 FOR SELECT USING (true);"}) == {}
    assert rls_blind_tables(["t1"], {"m/1.sql": "CREATE TABLE t1(id int);"}) == {}   # RLS never enabled: not blind


def test_the_protected_table_list_is_parsed_from_the_gate_script():
    tables = _l1_active_tables()
    assert "chart_facts" in tables and "chart_dashas" in tables and "chart_divisionals" in tables


# -- the held case ---------------------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason="held until #2984 merges: fix I-23(c)/incident F2 (schema-of-record parity for the "
           "chart_divisionals RLS repair, so a fresh database is not blind); SS chooses the fix",
)
def test_no_protected_l1_table_is_left_rls_enabled_without_a_usable_policy_by_the_migrations():
    blind = rls_blind_tables(_l1_active_tables(), _migration_texts())
    assert blind == {}, (
        "A database built from the migrations would recreate the chart_divisionals access incident "
        "(RLS enabled, no policy for any role that exists, owner is a NOLOGIN non-bypass role): "
        + "; ".join(f"{t}: {' | '.join(ev)}" for t, ev in sorted(blind.items()))
        + ". Production was repaired out of band (RLS disabled, 2026-10-01); no migration records it. "
          "Add a guarded, idempotent schema-of-record migration (never edit 002 or 1035) -- "
          "incident REVIEW Part III / decision Q-L1-01 (I-23c)."
    )
