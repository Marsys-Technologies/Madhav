"""test_e1_8_psql_parse.py — E1.8: `asset_census.psql()` must hand back exactly the rows and fields psql printed.

THE BUG (first real fresh census, S = 72e037515): `psql()` did `p.stdout.strip().split("\\n")` and
`ln.split(sep)` with `sep = "\\x1f"`. `str.strip()` treats U+001F (and U+001C..U+001E) as WHITESPACE, so the
whole-output strip ate the field separator of the FINAL row whenever that row's last field was empty (and the
first row's leading separator whenever its FIRST field was empty), yielding one field fewer — a
`ValueError: not enough values to unpack (expected 4, got 3)` in `catalog()` (the information_schema.columns
read, last row `l1_tajik_varsha_year_lords.computed_at`, empty default) that escaped every `except Unknown`
and ended the layer with exit 5. Every caller that does NOT unpack a fixed width would have been corrupted
SILENTLY instead (see PSQL_AUDIT.md in the PR description).

Two parts:
  * REAL POSTGRES (the off-production rehearsal cluster 127.0.0.1:55432, db `rehearsal`; skipped with a
    visible reason ONLY when it is unreachable): the real `psql()` subprocess path on inline VALUES queries
    (nothing is created; psql opens a new connection per call, so a TEMP table would not survive anyway).
  * PURE parser tests of `parse_psql_output` — never skipped (CI has no cluster).

Run:  python -m pytest platform/scripts/governance/__tests__/test_e1_8_psql_parse.py -q
"""
from __future__ import annotations

import getpass
import os
import pathlib
import shutil
import socket
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

REHEARSAL_HOST, REHEARSAL_PORT, REHEARSAL_DB = "127.0.0.1", 55432, "rehearsal"
_PG_BIN_FALLBACK = "/opt/homebrew/opt/postgresql@15/bin"


def _cluster_skip_reason() -> str | None:
    if not (shutil.which("psql") or os.path.exists(f"{_PG_BIN_FALLBACK}/psql")):
        return "no psql binary on PATH"
    try:
        with socket.create_connection((REHEARSAL_HOST, REHEARSAL_PORT), timeout=1):
            pass
    except OSError as exc:
        return (f"the off-production rehearsal cluster {REHEARSAL_HOST}:{REHEARSAL_PORT} is unreachable ({exc}); "
                "start it with platform/scripts/governance/rehearsal/rehearsal_cluster.sh start")
    return None


_SKIP = _cluster_skip_reason()
needs_cluster = pytest.mark.skipif(_SKIP is not None, reason=_SKIP or "")


@pytest.fixture
def rehearsal(monkeypatch):
    """Point the census's own psql() at the rehearsal cluster ONLY: every inherited PG*/DATABASE_URL name is
    removed, the connection is spelled out, and the server identity is proved before any test query runs."""
    for k in [k for k in os.environ if k.startswith("PG") or k in ("DATABASE_URL", "POSTGRES_URL")]:
        monkeypatch.delenv(k, raising=False)
    path = os.environ.get("PATH", "")
    if not shutil.which("psql"):
        path = f"{_PG_BIN_FALLBACK}:{path}"
    monkeypatch.setenv("PATH", path)
    monkeypatch.setenv("PGHOST", REHEARSAL_HOST)
    monkeypatch.setenv("PGPORT", str(REHEARSAL_PORT))
    monkeypatch.setenv("PGDATABASE", REHEARSAL_DB)
    monkeypatch.setenv("PGUSER", getpass.getuser())
    monkeypatch.setenv("PGPASSFILE", "/nonexistent/.pgpass")
    monkeypatch.setenv("PGSERVICEFILE", "/nonexistent/.pg_service.conf")
    ident = ac.psql("SELECT inet_server_port()::text, current_database()")
    assert ident == [[str(REHEARSAL_PORT), REHEARSAL_DB]], f"refusing to run: not the rehearsal cluster ({ident!r})"
    return ac


# ───────────────────────── real Postgres, real psql() ─────────────────────────

@needs_cluster
def test_real_psql_last_row_with_an_empty_trailing_field_keeps_its_field(rehearsal):
    rows = rehearsal.psql("SELECT a, b, c, d FROM (VALUES (1,'x','y','z'), (2,'p','q','')) v(a,b,c,d) ORDER BY a")
    assert rows == [["1", "x", "y", "z"], ["2", "p", "q", ""]]


@needs_cluster
def test_real_psql_first_row_with_an_empty_leading_field_keeps_its_field(rehearsal):
    rows = rehearsal.psql("SELECT a, b FROM (VALUES (1,'','x'), (2,'y','z')) v(o,a,b) ORDER BY o")
    assert rows == [["", "x"], ["y", "z"]]


@needs_cluster
def test_real_psql_a_result_of_only_empty_fields_is_one_row_not_none(rehearsal):
    assert rehearsal.psql("SELECT '', '', ''") == [["", "", ""]]
    assert rehearsal.psql("SELECT NULL::text, NULL::text") == [["", ""]]


@needs_cluster
def test_real_psql_an_empty_value_in_a_single_column_result_is_a_row(rehearsal):
    assert rehearsal.psql("SELECT a FROM (VALUES (1,'a'), (2,''), (3,'')) v(o,a) ORDER BY o") == [["a"], [""], [""]]
    assert rehearsal.scalar("SELECT ''") == ""      # present-but-empty is not "no rows"
    assert rehearsal.psql("SELECT 1 WHERE false") == []
    assert rehearsal.scalar("SELECT 1 WHERE false") is None


@needs_cluster
def test_real_psql_whitespace_inside_fields_survives(rehearsal):
    rows = rehearsal.psql("SELECT a, b FROM (VALUES (1,'  lead','trail  '), (2,E'\\t', ' ')) v(o,a,b) ORDER BY o")
    assert rows == [["  lead", "trail  "], ["\t", " "]]


@needs_cluster
def test_real_psql_a_value_with_an_embedded_newline_is_a_loud_ReadError_not_ragged_rows(rehearsal):
    with pytest.raises(rehearsal.ReadError):
        rehearsal.psql("SELECT 'a' || chr(10) || 'b', 'c', 'd'")


@needs_cluster
def test_real_psql_width_mismatch_is_a_ReadError(rehearsal):
    with pytest.raises(rehearsal.ReadError):
        rehearsal.psql("SELECT 'a', 'b'", width=3)
    assert rehearsal.psql("SELECT 'a', 'b'", width=2) == [["a", "b"]]


@needs_cluster
def test_real_catalog_read_of_the_table_that_crashed_the_fresh_L1_census(rehearsal):
    """The exact production crash: the columns read's final row is `computed_at | timestamp with time zone | ''`."""
    exists = rehearsal.scalar("SELECT (to_regclass('public.l1_tajik_varsha_year_lords') IS NOT NULL)::text")
    if exists not in ("t", "true"):
        pytest.skip("l1_tajik_varsha_year_lords is absent from the rehearsal schema (the crash needs that table's shape)")
    cat = rehearsal.catalog(["l1_tajik_varsha_year_lords"])
    assert cat["types"] is not None
    assert cat["types"]["l1_tajik_varsha_year_lords"]["computed_at"] == "timestamp with time zone"
    assert cat["cols"]["l1_tajik_varsha_year_lords"][-1] == "computed_at"


# ───────────────────────── pure parser: never skipped, no database ─────────────────────────

US, RS = "\x1f", "\x1e"


def _p(out, **kw):
    return ac.parse_psql_output(out, **kw)


def test_the_bug_the_last_rows_empty_trailing_field_is_kept():
    out = f"t{US}a{US}text{US}'x'::text\nt{US}b{US}timestamptz{US}\n"
    assert _p(out) == [["t", "a", "text", "'x'::text"], ["t", "b", "timestamptz", ""]]
    assert all(len(r) == 4 for r in _p(out))


def test_the_first_rows_empty_leading_field_is_kept_and_nothing_shifts():
    assert _p(f"{US}x{US}y\nq{US}r{US}s\n") == [["", "x", "y"], ["q", "r", "s"]]


def test_several_trailing_and_leading_empty_fields_all_survive():
    assert _p(f"{US}{US}a{US}{US}\n") == [["", "", "a", "", ""]]
    assert _p(f"a{US}{US}\nb{US}{US}\n") == [["a", "", ""], ["b", "", ""]]


def test_a_result_that_is_only_empty_fields_is_a_row_not_no_rows():
    assert _p(f"{US}{US}\n") == [["", "", ""]]
    assert _p(f"{US}\n{US}\n") == [["", ""], ["", ""]]
    assert _p(f"a{US}b\n{US}\n") == [["a", "b"], ["", ""]]


def test_a_single_column_empty_value_is_a_row_including_as_the_last_row():
    assert _p("\n") == [[""]]
    assert _p("a\n\n") == [["a"], [""]]
    assert _p("\na\n") == [[""], ["a"]]
    assert _p("a\n\n\n") == [["a"], [""], [""]]


def test_empty_output_is_no_rows_and_only_a_single_terminator_newline_is_removed():
    assert _p("") == []
    assert _p("x\n") == [["x"]]
    assert _p("x\n\n") == [["x"], [""]], "the second newline is an empty last row, not a second terminator"


def test_only_the_terminator_goes_other_whitespace_and_separator_like_characters_stay():
    assert _p("  a  \t\n") == [["  a  \t"]]
    assert _p(f" {US}b \n") == [[" ", "b "]]
    assert _p(f"{RS}{US}{RS}\n") == [[RS, RS]]            # U+001E is not the separator here and is never trimmed
    assert _p(f"a\x1c{US}\x1d\n") == [["a\x1c", "\x1d"]]
    assert _p(f"\t{US}\t\n") == [["\t", "\t"]]
    assert _p(f"a\r{US}b\r\n") == [["a\r", "b\r"]]       # CR is data, never a row break


def test_tabs_as_the_separator_keep_empty_fields_too():
    assert _p("a\tb\t\n\tc\td\n", sep="\t") == [["a", "b", ""], ["", "c", "d"]]


def test_the_record_separator_character_as_the_separator():
    assert _p(f"a{RS}{RS}\n{RS}b{RS}c\n", sep=RS) == [["a", "", ""], ["", "b", "c"]]


@pytest.mark.parametrize("out", [
    f"a{US}b\nc\n",                    # a short row
    f"a\nb{US}c\n",                    # a long row after a short one
    f"a{US}b\nc{US}d{US}e\n",
    f"a{US}b{US}c\nonly\n",            # a value with an embedded newline splits one row into two
])
def test_a_ragged_result_is_a_ReadError_never_padded_or_dropped(out):
    with pytest.raises(ac.ReadError):
        _p(out)


def test_a_declared_width_is_enforced_even_for_a_single_row():
    assert _p(f"a{US}b\n", width=2) == [["a", "b"]]
    with pytest.raises(ac.ReadError):
        _p(f"a{US}b\n", width=3)
    with pytest.raises(ac.ReadError):
        _p("a\n", width=2)
    with pytest.raises(ac.ReadError):
        _p(f"{US}\n", width=3)


def test_output_without_the_terminating_newline_is_truncation_a_ReadError():
    with pytest.raises(ac.ReadError):
        _p(f"a{US}b")
    with pytest.raises(ac.ReadError):
        _p(f"a{US}b\nc{US}")


def test_ReadError_is_an_Unknown_so_every_existing_per_check_guard_degrades_it():
    assert issubclass(ac.ReadError, ac.Unknown)


def test_psql_decodes_bytes_so_a_lone_CR_in_a_value_is_not_turned_into_a_newline(monkeypatch):
    class P:
        returncode = 0
        stdout = f"a\rb{US}c\n".encode()
        stderr = b""
    monkeypatch.setattr(ac.subprocess, "run", lambda *a, **k: P())
    assert ac.psql("SELECT 1") == [["a\rb", "c"]]


def test_psql_invalid_utf8_is_a_ReadError(monkeypatch):
    class P:
        returncode = 0
        stdout = b"\xff\xfe\n"
        stderr = b""
    monkeypatch.setattr(ac.subprocess, "run", lambda *a, **k: P())
    with pytest.raises(ac.ReadError):
        ac.psql("SELECT 1")


def test_psql_failure_still_raises_Unknown_with_the_first_stderr_line(monkeypatch):
    class P:
        returncode = 3
        stdout = b""
        stderr = "ERROR:  boom\nDETAIL: x\n".encode()
    monkeypatch.setattr(ac.subprocess, "run", lambda *a, **k: P())
    with pytest.raises(ac.Unknown, match="ERROR:  boom"):
        ac.psql("SELECT 1")


# ───────────────────────── catalog(): a malformed row is an honest failed read, not a crash ─────────────────────────

def _catalog_psql(types_rows):
    def psql(sql, sep="\x1f", timeout=None, width=None):
        if "information_schema.tables" in sql:
            return [["t"]]
        if "column_default" in sql:
            return types_rows
        if "information_schema.columns" in sql:
            return [["t", "a"], ["t", "b"]]
        return []
    return psql


def test_catalog_a_short_row_degrades_types_and_defaults_with_the_reason_instead_of_crashing(monkeypatch):
    monkeypatch.setattr(ac, "psql", _catalog_psql([["t", "a", "text", "'x'::text"], ["t", "b", "timestamptz"]]))
    cat = ac.catalog(["t"])                                   # used to raise ValueError (exit 5)
    assert cat["types"] is None and cat["defaults"] is None
    assert cat["cols"] == {"t": ["a", "b"]}, "the columns read is independent and unchanged"
    assert "expected 4" in cat["types_error"] and "3 field" in cat["types_error"]


def test_catalog_a_long_row_is_also_a_failed_read(monkeypatch):
    monkeypatch.setattr(ac, "psql", _catalog_psql([["t", "a", "text", "d", "extra"]]))
    assert ac.catalog(["t"])["types"] is None


def test_catalog_a_ReadError_from_psql_itself_degrades_the_same_way(monkeypatch):
    def psql(sql, sep="\x1f", timeout=None, width=None):
        if "column_default" in sql:
            raise ac.ReadError("psql row 2 of 2 has 3 field(s), expected 4")
        return _catalog_psql([])(sql)
    monkeypatch.setattr(ac, "psql", psql)
    cat = ac.catalog(["t"])
    assert cat["types"] is None and "3 field" in cat["types_error"]


def test_catalog_a_good_read_has_no_error_and_keeps_an_empty_last_default(monkeypatch):
    monkeypatch.setattr(ac, "psql", _catalog_psql([["t", "a", "text", "'x'::text"], ["t", "b", "timestamptz", ""]]))
    cat = ac.catalog(["t"])
    assert cat["types"] == {"t": {"a": "text", "b": "timestamptz"}} and cat["defaults"] == {"t": {"a": "'x'::text"}}
    assert cat["types_error"] is None


def test_catalog_the_failed_read_reason_reaches_the_cells_that_needed_the_types(monkeypatch):
    monkeypatch.setattr(ac, "psql", _catalog_psql([["t", "a", "text"]]))
    cat = ac.catalog(["t"])
    decl = {"prose_fields": ["a"]}
    r = {"target_table": "t", "count_sql": "SELECT count(*) FROM t"}
    out = ac._measure_prose("bg_x", decl, r, None, cat, [], {}, [], None)
    nd = out["Null.schema_default"]
    assert nd["v"] == ac.NO_DET and "column types/defaults read failed" in nd["measured"] and "expected 4" in nd["measured"], nd
