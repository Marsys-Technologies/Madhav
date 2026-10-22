"""test_check_f4_exact_reads.py — the SR-F4-STORE-EXACT amend-1 guard (a REAL column is read `::float8`, never as the driver's default text).

Source of the rule: PostgreSQL stores `REAL` as IEEE-754 binary32; the driver's default text read of it is the SHORTEST DECIMAL that round-trips it, a different double
(0.1 for the stored 0.100000001490116…), so a verifier comparing it inside a half-float4-spacing tolerance double-counts the rounding (PRETR-early D-C). `::float8` is
the exact widening.

The guard is proven here to be able to FAIL (a planted uncast SELECT, one per claim), to PASS (the cast forms and the non-reads), to see the real tree (every fixed production
reader, reverted, is caught; the tree as it stands is clean), and not to rot (a stale exemption fails; the REAL-column table is re-derived from the migrations).
"""
from __future__ import annotations

import importlib.util
import pathlib
import subprocess
import sys

import pytest

GOV = pathlib.Path(__file__).resolve().parent.parent
REPO = GOV.parent.parent.parent
TOOL = GOV / "check_f4_exact_reads.py"

_spec = importlib.util.spec_from_file_location("check_f4_exact_reads_under_test", TOOL)
G = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = G
_spec.loader.exec_module(G)

KERNEL = "platform/python-sidecar/services/gochara_kernel"


def _flagged(src: str, rel: str = f"{KERNEL}/planted.py") -> list:
    v, _ = G.check_python_source(src, rel, exempt=())
    return v


# ── the guard can FAIL: a planted uncast read, one per REAL column family ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("table,col", [
    ("ka_gochara_eval_window", "score"), ("ka_gochara_eval_window", "evidence_for"), ("ka_gochara_eval_window", "evidence_against"),
    ("ka_gochara_eval_window", "severity"), ("ka_gochara_eval_window", "objective_value"),
    ("ka_gochara_relationship_record", "evidence_for_occurrence"), ("ka_gochara_relationship_record", "evidence_against_occurrence"),
    ("ka_gochara_relationship_record", "severity"), ("ka_gochara_contact", "delta_lambda"), ("ka_gochara_contact", "delta_t"),
    ("ka_gochara_sky_event", "delta_lambda"), ("ka_gochara_near_miss", "delta_t"), ("ka_gochara_factor", "range_lower"),
])
def test_planted_uncast_select_fails(table, col):
    src = f'def f(conn):\n    return conn.execute("SELECT x.id, x.{col} FROM public.{table} x WHERE x.chart_id = %s", (1,))\n'
    (v,) = _flagged(src)
    assert v.column == col and "without ::float8" in v.reason


def test_planted_uncast_select_in_a_concatenated_statement_fails():
    src = ('def f(conn):\n    return conn.execute(\n        "SELECT window_id::text, score,"\n        " severity FROM public.ka_gochara_eval_window"\n'
           '        " WHERE chart_id = %s", (1,))\n')
    assert {v.column for v in _flagged(src)} == {"score", "severity"}


def test_planted_uncast_select_in_an_fstring_statement_fails():
    src = 'def f(conn, w):\n    return conn.execute(f"SELECT {w}, objective_value FROM public.ka_gochara_eval_window")\n'
    assert [v.column for v in _flagged(src)] == ["objective_value"]


def test_the_default_text_cast_is_not_an_exact_read():
    assert _flagged('q = "SELECT delta_lambda::text FROM public.ka_gochara_contact"\n')


def test_planted_star_select_over_a_real_table_fails():
    for q in ("SELECT * FROM public.ka_gochara_near_miss", "SELECT r.*, 1 FROM public.ka_gochara_relationship_record r", "SELECT DISTINCT c.* FROM public.ka_gochara_contact c"):
        (v,) = _flagged(f'q = "{q}"\n')
        assert v.column == "*", q


def test_planted_uncast_select_list_fragment_fails():
    src = ('_COLUMNS = "w.window_id::text, w.score, w.severity::float8, w.null_states_used"\n'
           'def f(conn):\n    return conn.execute("SELECT " + _COLUMNS + " FROM public.ka_gochara_eval_window w")\n')
    assert [v.column for v in _flagged(src)] == ["score"]


def test_a_second_select_inside_an_exempt_looking_statement_is_still_caught():
    src = 'q = "SELECT a FROM public.ka_gochara_contact WHERE id IN (SELECT x.delta_lambda FROM public.ka_gochara_contact x)"\n'
    assert [v.column for v in _flagged(src)] == ["delta_lambda"]


# ── the guard can PASS: exact reads and non-reads ─────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("sql", [
    "SELECT c.contact_id, c.delta_lambda::float8 FROM public.ka_gochara_contact c",
    "SELECT w.score::float8, w.severity::double precision FROM public.ka_gochara_eval_window w",
    "SELECT float4send(w.score) FROM public.ka_gochara_eval_window w",
    "SELECT (score IS NOT NULL), (evidence_for IS NULL OR objective_value IS NOT NULL), count(*) FROM public.ka_gochara_eval_window GROUP BY 1, 2",   # NULL tests are not value reads
    "SELECT window_id FROM public.ka_gochara_eval_window WHERE score IS NOT NULL AND severity > 0 ORDER BY score",                                  # predicates / ordering are not reads
    "SELECT count(*) FROM public.ka_gochara_eval_window",
    "SELECT qualification ->> 'score' FROM public.ka_gochara_eval_window",                                                                          # a JSON key named like a column
    "SELECT x AS score FROM public.ka_gochara_eval_window",                                                                                         # an output alias
    "SELECT *, delta_t::float8 AS delta_t FROM public.ka_gochara_near_miss",                                                                        # a star that re-selects every REAL column exactly
    "SELECT * FROM unnest(%s::text[], %s::text[])",                                                                                                 # a star over a non-REAL source
    "SELECT severity, score FROM public.kala_obstruction",                                                                                          # same names, a table with no REAL column of ours
    "SELECT to_jsonb(t) FROM public.ka_gochara_factor t",                                                                                           # whole-row JSON digest preimage: not a value read
])
def test_exact_reads_and_non_reads_pass(sql):
    assert _flagged(f'q = "{sql}"\n') == [], sql


def test_a_docstring_that_mentions_a_select_is_not_scanned():
    src = 'def f():\n    """SELECT score FROM public.ka_gochara_eval_window — documented, not executed"""\n'
    assert _flagged(src) == []


# ── the guard sees the REAL tree ──────────────────────────────────────────────────────────────────────────────────────────────────────

# (file, the exact `::float8` cast the fix added, what the planted reversion turns it into): each fixed production reader, reverted, must be caught.
FIXED_READERS = [
    ("window_verifier.py", "c.delta_lambda::float8", "c.delta_lambda"),
    ("record_verifier.py", "c.delta_lambda::float8", "c.delta_lambda"),
    ("contact_certify.py", "c.delta_lambda::float8", "c.delta_lambda"),
    ("record_derivation.py", "r.evidence_for_occurrence::float8", "r.evidence_for_occurrence"),
    ("scope_response.py", "objective_value::float8, qualification, path_id\"", "objective_value, qualification, path_id\""),
    ("serving_reader.py", "w.score::float8", "w.score"),
    ("near_miss_verifier.py", ",delta_t::float8 AS delta_t", ""),
]


@pytest.mark.parametrize("fname,cast,reverted", FIXED_READERS)
def test_each_fixed_reader_reverted_to_a_text_read_is_caught(fname, cast, reverted):
    rel = f"{KERNEL}/{fname}"
    src = (REPO / rel).read_text()
    assert cast in src, (fname, cast)
    clean, _ = G.check_python_source(src, rel)
    assert clean == [], clean
    bad, _ = G.check_python_source(src.replace(cast, reverted), rel)
    assert bad, f"reverting {fname} to a text read of a REAL was not caught"


def test_the_round_1_window_verifier_read_reverted_is_caught():
    import re
    rel = f"{KERNEL}/window_verifier.py"
    src = (REPO / rel).read_text()
    assert G.check_python_source(src, rel)[0] == []
    reverted = re.sub(r"\b(score|evidence_for|evidence_against|severity)::float8", r"\1", src)
    assert reverted != src
    bad, _ = G.check_python_source(reverted, rel)
    assert {v.column for v in bad} >= {"score", "evidence_for", "evidence_against", "severity"}


@pytest.fixture(scope="module")
def tree_scan():
    return G.scan_tree(REPO)


def test_the_tree_as_it_stands_is_clean_and_has_no_stale_exemption(tree_scan):
    violations, stale = tree_scan
    assert violations == [], "\n".join(map(str, violations))
    assert stale == []


def test_the_scan_really_reads_the_kernel_files():
    """An empty scan would be 'clean' too: the roots must contain the verifier / reader modules the audit named."""
    scanned = {p.name for root in G.ROOTS for p in (REPO / root).rglob("*.py")}
    assert {"window_verifier.py", "record_verifier.py", "contact_certify.py", "record_derivation.py", "scope_response.py", "serving_reader.py",
            "near_miss_verifier.py", "window_gate.py", "numerical_window_gate.py", "seal_brief.py"} <= scanned


# ── the guard does not rot ────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_stale_exemption_fails_the_run():
    _, stale = G.scan_tree(REPO, exempt=G.EXEMPT + (("services/gochara_kernel/window_gate.py", "no such statement", "stale"),))
    assert stale == ["services/gochara_kernel/window_gate.py / 'no such statement'"]


def test_an_exemption_covers_its_statement_only():
    rel = f"{KERNEL}/window_gate.py"
    src = (REPO / rel).read_text() + '\nBAD = "SELECT w.score FROM public.ka_gochara_eval_window w"\n'
    v, used = G.check_python_source(src, rel)
    assert [x.column for x in v] == ["score"]
    assert used, "the real window_gate digest preimage statements stay exempt"


def test_every_exemption_names_a_reason():
    assert all(len(why) > 40 for _, _, why in G.EXEMPT)


def test_the_real_column_table_is_the_migrations_truth():
    """REAL_COLUMNS is not a guess: it equals the REAL columns the `ka_gochara_*` migrations declare (a new REAL column must teach the guard)."""
    assert G.declared_real_columns(REPO / "platform" / "migrations") == G.REAL_COLUMNS


# ── the command line ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _run(root: pathlib.Path):
    return subprocess.run([sys.executable, "-I", str(TOOL), "--repo-root", str(root)], capture_output=True, text=True, timeout=120)


def test_cli_passes_on_the_repo():
    r = _run(REPO)
    assert r.returncode == 0, r.stdout + r.stderr


def test_cli_fails_on_a_planted_uncast_select(tmp_path):
    d = tmp_path / "platform" / "python-sidecar" / "services" / "gochara_kernel"
    d.mkdir(parents=True)
    (d / "planted.py").write_text('def f(conn):\n    return conn.execute("SELECT w.score FROM public.ka_gochara_eval_window w")\n')
    r = _run(tmp_path)
    assert r.returncode == 1 and "F4-LOSSY-READ" in r.stdout and "planted.py:2" in r.stdout, r.stdout
