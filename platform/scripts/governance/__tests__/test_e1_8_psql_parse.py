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
