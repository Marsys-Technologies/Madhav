"""
Migration 1215 (Suvarna Track I-8): ka_avadhi `integrity_check_sql` scoped to the canonical chart,
and conjunct (b) listing 'chara_karaka' instead of 'chara'.

DB-FREE (no database of any kind is touched). What this proves, and what it does not:
  * PROVES (static, on the migration text): every one of the five conjuncts (a)-(e) carries the
    canonical-chart scope predicate on its OUTER row set, as an AND (never an OR); the scope literal is
    the canonical chart id and is the same literal ka_yojaka's 1019/1022 use; (b) lists exactly the
    L1/writer dasha-system vocabulary (ALL_DASHA_SYSTEMS, 'chara_karaka'); NOTHING ELSE changed versus
    1023's live text (golden transformation: 1023 + the six scope/vocabulary edits == 1215, comments
    ignored), so no conjunct was weakened; the SQL takes no bind parameter (the runner passes none); the
    migration is registry-only, lock_timeout-guarded, idempotent, has loud pre/post assertions, and its
    number is free.
  * HAS TEETH: `_scope_findings` is shown to flag a mutated SQL missing the scope in any one conjunct
    (five mutants), a wrong or phantom chart literal, an OR-widened scope and the stale 'chara' literal.
  * DOES NOT PROVE the live registry state (that is the read-only before/after SQL saved next to the
    Track I evidence) nor the check's boolean result on live rows (needs a DB: out of scope here). The
    optional pglast test additionally parses the SQL with the real PostgreSQL grammar when pglast is
    installed (skips otherwise: it is a syntax cross-check, not the primary gate).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_MIG_DIR = _REPO / "platform" / "migrations"
_SUPA_DIR = _REPO / "platform" / "supabase" / "migrations"
_MIG_NAME = "1215_suvarna_i8_ka_avadhi_integrity_check_chart_scope.sql"
_MIG = _MIG_DIR / _MIG_NAME
_PREV = _MIG_DIR / "1023_nirmana_l3_ka_avadhi_integrity_conjunct_d_graha_code_fix.sql"
_YOJAKA_1019 = _MIG_DIR / "1019_nirmana_l3_ka_yojaka_integrity_check_scope.sql"
_YOJAKA_1022 = _MIG_DIR / "1022_nirmana_l3_ka_yojaka_integrity_check_scope_ab.sql"
_RUNNER = _REPO / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "asset_runner.py"
_TREE_WALK = _REPO / "platform" / "python-sidecar" / "services" / "ka_dasha_kala" / "tree_walk.py"

CANONICAL = "482012f1-710e-4a25-994a-93821f5871aa"
PHANTOM = "362f9f17"
# conjunct -> alias of the OUTER row set that must carry the chart scope
_OUTER_ALIAS = {"a": "a", "b": "d", "c": "a", "d": "a", "e": "a"}


# ---------------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------------
def _ck_body(sql_text: str) -> str:
    s = sql_text.index("$ck$")
    e = sql_text.rindex("$ck$")
    assert s != e, "no $ck$-delimited detector SQL"
    return sql_text[s + 4 : e]


def _strip_comments(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def _collapse(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip()


def _conjunct_blocks(body: str) -> dict[str, str]:
    """Split the detector body on its `-- (a)` ... `-- (e)` header comments."""
    marks = list(re.finditer(r"^[ \t]*-- \(([a-e])\)", body, re.M))
    letters = [m.group(1) for m in marks]
    assert letters == list("abcde"), f"conjunct markers are {letters}"
    blocks = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        blocks[m.group(1)] = body[m.start() : end]
    return blocks


def _scope_findings(body: str, canonical: str = CANONICAL) -> list[str]:
    """Every problem with the chart scoping of a ka_avadhi detector body ([] == clean)."""
    out: list[str] = []
    try:
        blocks = _conjunct_blocks(body)
    except AssertionError as exc:
        return [f"structure: {exc}"]
    for letter, block in blocks.items():
        code = _strip_comments(block)
        w = re.search(r"\bWHERE\b", code)
        if not w:
            out.append(f"({letter}) no WHERE")
            continue
        rest = code[w.end():]
        alias = _OUTER_ALIAS[letter]
        m = re.match(rf"[ \t]*{alias}\.chart_id\s*=\s*'([0-9a-f-]+)'[ \t]*\n(\s*)(\w+)", rest)
        if not m:
            out.append(f"({letter}) outer WHERE does not start with {alias}.chart_id = '<uuid>'")
            continue
        if m.group(1) != canonical:
            out.append(f"({letter}) scope literal is {m.group(1)}, not the canonical chart")
        if m.group(3).upper() != "AND":
            out.append(f"({letter}) scope is joined with {m.group(3)}, not AND")
    n = len(re.findall(r"\b[ad]\.chart_id\s*=\s*'[0-9a-f-]+'", _strip_comments(body)))
    if n != 5:
        out.append(f"expected exactly 5 chart-literal predicates, found {n}")
    # (b) vocabulary
    b = _strip_comments(blocks.get("b", ""))
    if "'chara_karaka'" not in b:
        out.append("(b) lacks 'chara_karaka'")
    if re.search(r"'chara'\s*[,\]\)]", b):
        out.append("(b) still lists the stale 'chara' literal")
    return out


def _all_dasha_systems() -> set[str]:
    src = _TREE_WALK.read_text()
    m = re.search(r"ALL_DASHA_SYSTEMS\s*=\s*frozenset\(\{(.*?)\}\)", src, re.S)
    assert m, "ALL_DASHA_SYSTEMS not found"
    return set(re.findall(r"\"([a-z_]+)\"", m.group(1)))


def _b_systems(body: str) -> set[str]:
    b = _strip_comments(_conjunct_blocks(body)["b"])
    m = re.search(r"ARRAY\[(.*?)\]", b, re.S)
    assert m, "(b) system array not found"
    return set(re.findall(r"'([a-z_]+)'", m.group(1)))


@pytest.fixture(scope="module")
def mig_text() -> str:
    return _MIG.read_text()


@pytest.fixture(scope="module")
def body(mig_text) -> str:
    return _ck_body(mig_text)


# ---------------------------------------------------------------------------------------------------
# scope, vocabulary, golden transformation
# ---------------------------------------------------------------------------------------------------
def test_every_conjunct_is_scoped_to_the_canonical_chart(body):
    assert _scope_findings(body) == []


def test_scope_literal_is_the_canonical_chart_and_matches_ka_yojaka(mig_text):
    assert CANONICAL in mig_text
    assert PHANTOM not in mig_text, "the dead phantom chart id must never be written"
    for f in (_YOJAKA_1019, _YOJAKA_1022):
        t = f.read_text()
        assert f"chart_id = '{CANONICAL}'" in t, f"{f.name}: ka_yojaka scope shape changed"
    # same mechanism: a bare literal, no placeholder
    assert re.search(rf"\ba\.chart_id = '{CANONICAL}'", _strip_comments(mig_text))


def test_conjunct_b_system_array_equals_the_writer_vocabulary(body):
    assert _b_systems(body) == _all_dasha_systems()
    assert "chara_karaka" in _all_dasha_systems()


def test_previous_text_had_the_stale_chara_literal():
    # documents the defect this migration fixes (and keeps the golden test honest about its base)
    prev = _strip_comments(_ck_body(_PREV.read_text()))
    assert "'chara'," in prev and "chara_karaka" not in prev


def test_nothing_else_changed_versus_1023_golden_transformation(body):
    """1023's live text + exactly the six scope/vocabulary edits == 1215's text (comments ignored).

    This is the 'do not weaken what the check guards' proof: every predicate of every conjunct survives;
    only the row set narrows and 'chara' becomes 'chara_karaka'.
    """
    C = f"'{CANONICAL}'"
    old = _collapse(_strip_comments(_ck_body(_PREV.read_text())))
    edits = [
        ("SELECT 1 FROM kala_avadhi a WHERE NOT EXISTS ( SELECT 1 FROM chart_dashas d",
         f"SELECT 1 FROM kala_avadhi a WHERE a.chart_id = {C} AND NOT EXISTS ( SELECT 1 FROM chart_dashas d"),
        ("SELECT 1 FROM chart_dashas d WHERE d.ayanamsha_id = 'lahiri_chitrapaksha' AND d.level_n IN (1, 2)",
         f"SELECT 1 FROM chart_dashas d WHERE d.chart_id = {C} AND d.ayanamsha_id = 'lahiri_chitrapaksha' AND d.level_n IN (1, 2)"),
        ("'chara','naisargika'", "'chara_karaka','naisargika'"),
        ("SELECT 1 FROM kala_avadhi a WHERE a.lord_graha = ANY",
         f"SELECT 1 FROM kala_avadhi a WHERE a.chart_id = {C} AND a.lord_graha = ANY"),
        ("AS r WHERE upper(r->>'fact_subject') IS DISTINCT FROM (",
         f"AS r WHERE a.chart_id = {C} AND (upper(r->>'fact_subject') IS DISTINCT FROM ("),
        ("f.fact_id = r->>'fact_id') )", "f.fact_id = r->>'fact_id') ) )"),
        ("AS p WHERE NOT EXISTS (", f"AS p WHERE a.chart_id = {C} AND NOT EXISTS ("),
    ]
    expected = old
    for before, after in edits:
        assert expected.count(before) == 1, f"edit anchor not unique in 1023 text: {before!r}"
        expected = expected.replace(before, after)
    assert _collapse(_strip_comments(body)) == expected


def test_all_five_conjuncts_and_their_predicates_survive(body):
    code = _collapse(_strip_comments(body))
    for needle in (
        "d.lord_graha = a.lord_graha",                      # (a) lord match
        "d.ayanamsha_id = 'lahiri_chitrapaksha'",           # (a)/(b) canonical ayanamsha
        "a.period_start = d.start_date",                    # (b) coverage
        "jsonb_array_length(COALESCE(a.dossier->'lord_condition_fact_refs','[]'::jsonb)) = 0",  # (c)
        "WHEN 'RAHU' THEN 'RAH_MEAN'",                      # (d) vocabulary CASE
        "f.fact_id = r->>'fact_id'",                        # (d) ref resolves
        "bp.pratijna_id::text = p",                         # (e)
        "AS integrity_passed",
    ):
        assert needle in code, needle
    assert len(re.findall(r"-- \([a-e]\)", body)) == 5


# ---------------------------------------------------------------------------------------------------
# runner contract: the SQL cannot take a chart parameter
# ---------------------------------------------------------------------------------------------------
def test_runner_executes_integrity_sql_without_parameters():
    src = _RUNNER.read_text()
    assert re.search(r"cur\.execute\(integrity_sql\)", src), (
        "runner no longer executes integrity_sql parameter-free: the hard-coded chart literal "
        "mechanism (same as ka_yojaka 1019/1022) must be re-examined"
    )


def test_detector_sql_has_no_bind_placeholder_and_is_read_only(body):
    code = _strip_comments(body)
    assert not re.search(r"%s|%\(|\$\d", code)
    assert not re.search(r":[A-Za-z_]", code.replace("::", "")), "named bind placeholder"
    assert not re.search(
        r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE)\b", code, re.I
    )


# ---------------------------------------------------------------------------------------------------
# migration hygiene
# ---------------------------------------------------------------------------------------------------
def test_number_is_unique_in_suvarna_range_and_not_the_held_1211():
    n = _MIG.name.split("_", 1)[0]
    assert n == "1215" and 1200 <= int(n) <= 1299 and n != "1211"
    same = [p.name for d in (_MIG_DIR, _SUPA_DIR) if d.is_dir() for p in d.glob(f"{n}_*.sql")]
    assert same == [_MIG_NAME], same


def test_registry_only_lock_timeout_idempotent_with_loud_assertions(mig_text):
    code = _strip_comments(mig_text)
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", code, re.M | re.I), "migrate.ts owns the transaction"
    assert "SET LOCAL lock_timeout = '5s';" in code
    assert code.index("SET LOCAL lock_timeout") < code.index("UPDATE asset_registry")
    # exactly one UPDATE, on asset_registry, targeted by asset_id (never a blanket update)
    assert len(re.findall(r"\bUPDATE\b", code)) == 1
    assert re.search(r"UPDATE asset_registry SET integrity_check_sql = \$ck\$", code)
    assert re.search(r"\$ck\$\s*WHERE asset_id = 'ka_avadhi';", code)
    # nothing else is written
    outside_do = re.sub(r"\$(pre|post)\$.*?\$\1\$", "", code, flags=re.S)
    assert not re.search(r"\b(INSERT|DELETE|DROP|ALTER|TRUNCATE|CREATE)\b", outside_do, re.I)
    # loud pre/post assertions (CLAUDE.md N.4: never a silent no-op)
    assert "$pre$" in code and "$post$" in code and code.count("RAISE EXCEPTION") == 2
    assert "'chara_karaka'" in code.split("$post$")[1] or "''chara_karaka''" in code.split("$post$")[1]
    # idempotent: the only write is a constant assignment
    assert "now()" not in code.lower() and "random" not in code.lower()


def test_pglast_parses_the_whole_migration_and_scope_is_in_the_ast(mig_text):
    pglast = pytest.importorskip("pglast")
    stmts = pglast.parse_sql(mig_text)
    assert [type(s.stmt).__name__ for s in stmts] == [
        "VariableSetStmt", "DoStmt", "UpdateStmt", "DoStmt",
    ]
    # the detector itself must parse as one SELECT
    pglast.parse_sql(_ck_body(mig_text))


# ---------------------------------------------------------------------------------------------------
# the checker has teeth: mutated SQL must be flagged
# ---------------------------------------------------------------------------------------------------
_SCOPE_LINE = re.compile(rf"\b[ad]\.chart_id = '{CANONICAL}'\n\s*AND ")


def _drop_nth_scope(body: str, n: int) -> str:
    hits = list(_SCOPE_LINE.finditer(_strip_comments(body)))
    assert len(hits) == 5
    # operate on the comment-bearing text: find the n-th literal occurrence
    idx = [m.start() for m in re.finditer(rf"\b[ad]\.chart_id = '{CANONICAL}'", body)]
    assert len(idx) == 5
    s = idx[n]
    e = body.index("AND ", s) + 4
    return body[:s] + body[e:]


@pytest.mark.parametrize("n,letter", list(enumerate("abcde")))
def test_mutant_missing_scope_in_one_conjunct_is_flagged(body, n, letter):
    mutated = _drop_nth_scope(body, n)
    findings = _scope_findings(mutated)
    assert findings, f"mutant dropping the scope of ({letter}) was NOT flagged"


def test_mutant_wrong_or_phantom_chart_literal_is_flagged(body):
    assert _scope_findings(body.replace(CANONICAL, "1c826d5a-0000-0000-0000-000000000000", 1))
    assert _scope_findings(body.replace(CANONICAL, "362f9f17-0000-0000-0000-000000000000"))


def test_mutant_or_widened_scope_is_flagged(body):
    widened = body.replace(f"a.chart_id = '{CANONICAL}'\n      AND NOT EXISTS (\n      SELECT 1 FROM chart_dashas",
                           f"a.chart_id = '{CANONICAL}'\n      OR NOT EXISTS (\n      SELECT 1 FROM chart_dashas")
    assert widened != body and _scope_findings(widened)


def test_mutant_stale_chara_literal_is_flagged(body):
    mutated = body.replace("'chara_karaka'", "'chara'")
    assert mutated != body and _scope_findings(mutated)
