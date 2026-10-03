"""test_e5_3_deps_sql_parity.py -- Suvarna E5.3: DEPS_SQL is the runner's dependency query, byte for byte modulo whitespace.

suvarna_level_wave.DEPS_SQL is a copy of the statement in the FROZEN pipeline/orchestrator/asset_runner.py
`deps_unsatisfied` (DEP-ASSERT). The dispatcher's external-dependency pre-check is only as good as that copy. This file
holds the parity check against the COMMITTED runner text (`git show HEAD:<path>`: local objects, no network, not the
working tree) and seeded defects proving the check can fail. There is no skip anywhere: a check that cannot read the
runner text FAILS.
"""
from __future__ import annotations

import pathlib
import re
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suvarna_level_wave as slw  # noqa: E402

REPO = HERE.parents[3]
PINNED_REF = "HEAD"        # the commit the working tree is on: present in every checkout, shallow or not, offline


@pytest.fixture(scope="module")
def runner_text() -> str:
    return slw.runner_text_at_ref(REPO, PINNED_REF)


def collapse(sql: str) -> str:
    return " ".join(sql.split())


def runner_sql(text: str) -> str:
    return slw.extract_runner_deps_sql(text)


def mutate(text: str, old: str, new: str) -> str:
    """Replace `old` inside the runner's SQL literal only, asserting it is there exactly once (a seeded defect that did not
    apply would make its test vacuous)."""
    sql = runner_sql(text)
    assert sql.count(old) == 1, f"seed target {old!r} found {sql.count(old)} times in the runner SQL"
    return text.replace(sql, sql.replace(old, new))


# ───────────────────────── the parity itself (committed text) ─────────────────────────

def test_deps_sql_equals_the_committed_runner_statement(runner_text):
    extracted = runner_sql(runner_text)
    assert extracted.strip(), "extractor returned nothing"
    assert slw.deps_sql_matches_runner(runner_text), (
        "DEPS_SQL has drifted from asset_runner.deps_unsatisfied:\n"
        f"  dispatcher: {slw.collapse_sql_whitespace(slw.DEPS_SQL)}\n  runner:     {slw.collapse_sql_whitespace(extracted)}")
    assert slw.collapse_sql_whitespace(slw.DEPS_SQL) == slw.collapse_sql_whitespace(extracted)


def test_the_extracted_statement_is_the_whole_query_not_a_fragment(runner_text):
    c = slw.collapse_sql_whitespace(runner_sql(runner_text))
    assert c.startswith("SELECT dep.asset_id, reg.asset_kind, t.state, f.freshness_state FROM unnest(%s::text[]) AS dep(asset_id)")
    assert c.endswith("LIMIT 1 ) f ON true")
    assert c.count("LEFT JOIN LATERAL") == 2 and c.count("%s") == 5 and c.count("LIMIT 1") == 2


def test_the_runner_executes_the_statement_it_was_extracted_from_with_four_chart_ids(runner_text):
    """DEPS_SQL is executed with (deps, chart, chart, chart, chart); the runner does the same. Pins the parameter shape the
    SQL text parity does not cover."""
    body = runner_text[runner_text.index("def deps_unsatisfied"):]
    assert "(deps, chart_id, chart_id, chart_id, chart_id)" in body.split("def ", 2)[1]
    assert "cur.execute(DEPS_SQL, (wanted, chart_id, chart_id, chart_id, chart_id))" in \
        pathlib.Path(slw.__file__).read_text(encoding="utf-8")


def test_the_pinned_ref_text_is_the_committed_text_and_works_without_network(runner_text):
    again = subprocess.run(["git", "-C", str(REPO), "show", f"{PINNED_REF}:{slw.ASSET_RUNNER_REL}"],
                           capture_output=True, text=True, check=True, timeout=60).stdout
    assert again == runner_text and "def deps_unsatisfied" in runner_text


# ───────────────────────── seeded defects: a changed runner is detected ─────────────────────────

@pytest.mark.parametrize("old,new", [
    ("(at.chart_id IS NOT DISTINCT FROM %s) DESC", "(at.chart_id IS NOT DISTINCT FROM %s) ASC"),     # ASC instead of DESC
    ("at.last_built_at DESC NULLS LAST", "at.last_built_at ASC NULLS LAST"),
    ("at.last_built_at DESC NULLS LAST", "at.last_built_at DESC"),                                     # NULLS LAST dropped
    ("af.observed_at DESC", "af.observed_at ASC"),
    ("(at.chart_id IS NOT DISTINCT FROM %s OR at.chart_id IS NULL)", "(at.chart_id IS NOT DISTINCT FROM %s)"),  # OR ... IS NULL dropped
    ("(af.chart_id IS NOT DISTINCT FROM %s OR af.chart_id IS NULL)", "(af.chart_id IS NOT DISTINCT FROM %s)"),
    ("at.chart_id IS NOT DISTINCT FROM %s OR", "at.chart_id = %s OR"),
    ("SELECT state FROM asset_throughput at", "SELECT state FROM asset_throughput_v2 at"),
    ("SELECT freshness_state FROM asset_freshness af", "SELECT freshness_state FROM asset_freshness af_x"),
    ("LEFT JOIN asset_registry reg", "JOIN asset_registry reg"),
    ("reg.asset_kind", "reg.asset_type"),
    ("f.freshness_state", "f.state"),
    ("unnest(%s::text[]) AS dep(asset_id)", "unnest(%s::text[]) AS dep(asset)"),
    ("LIMIT 1 ) t ON true", "LIMIT 2 ) t ON true"),
    ("WHERE at.asset_id = dep.asset_id", "WHERE at.asset_id <> dep.asset_id"),
])
def test_a_modified_runner_statement_is_detected_as_different(runner_text, old, new):
    sql = runner_sql(runner_text)
    flat = collapse(sql)                                  # seeds are written against the whitespace-collapsed statement
    assert flat.count(collapse(old)) == 1, f"seed {old!r} is not applicable exactly once (a vacuous seed proves nothing)"
    mutated = runner_text.replace(sql, flat.replace(collapse(old), collapse(new)))
    assert mutated != runner_text
    assert slw.deps_sql_matches_runner(mutated) is False
    assert slw.deps_sql_matches_runner(runner_text) is True          # the unmodified text still matches


def test_a_modified_dispatcher_statement_is_detected_as_different(runner_text):
    for old, new in [("DESC", "ASC"), (" OR at.chart_id IS NULL", ""), ("NULLS LAST", ""), ("LEFT JOIN", "JOIN")]:
        assert old in slw.DEPS_SQL
        assert slw.deps_sql_matches_runner(runner_text, slw.DEPS_SQL.replace(old, new, 1)) is False


def test_whitespace_only_changes_do_not_matter(runner_text):
    sql = runner_sql(runner_text)
    reflowed = "\n\n   ".join(sql.split()) + "\n"
    assert slw.deps_sql_matches_runner(runner_text.replace(sql, reflowed)) is True
    assert slw.deps_sql_matches_runner(runner_text, slw.DEPS_SQL.replace("\n", "\n\n\t")) is True


def test_a_token_changed_only_in_case_or_inner_spacing_is_still_a_difference(runner_text):
    # the comparison is whitespace-collapsing, NOT case-insensitive and NOT token-gluing
    assert slw.deps_sql_matches_runner(mutate(runner_text, "NULLS LAST", "nulls last")) is False
    assert slw.deps_sql_matches_runner(mutate(runner_text, "AS dep(asset_id)", "AS dep (asset_id)")) is False


def test_parameter_count_change_is_detected(runner_text):
    assert slw.deps_sql_matches_runner(mutate(runner_text, "ORDER BY (at.chart_id IS NOT DISTINCT FROM %s) DESC",
                                              "ORDER BY (at.chart_id IS NOT DISTINCT FROM 'x') DESC")) is False


# ───────────────────────── seeded defects: an unreadable runner RAISES (never passes, never skips) ─────────────────────────

def test_empty_and_unparseable_text_raise():
    for bad in ("", "   \n", "def broken(:\n", "x = 'unterminated\n"):
        with pytest.raises(slw.RunnerSqlExtractionError):
            slw.extract_runner_deps_sql(bad)
        with pytest.raises(slw.RunnerSqlExtractionError):
            slw.deps_sql_matches_runner(bad)


def test_missing_renamed_or_duplicated_function_raises(runner_text):
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.extract_runner_deps_sql(runner_text.replace("def deps_unsatisfied(", "def deps_unsatisfied_renamed("))
    dup = runner_text + "\n\ndef deps_unsatisfied(cur):\n    return []\n"
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.extract_runner_deps_sql(dup)


def test_function_without_the_statement_raises():
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.extract_runner_deps_sql("def deps_unsatisfied(cur, c, a):\n    cur.execute('SELECT 1')\n    return []\n")


def test_two_candidate_statements_raise_not_pick_one(runner_text):
    sql = runner_sql(runner_text)
    two = runner_text.replace(sql, sql) + ""
    body_end = two.index("def deps_unsatisfied")
    injected = two[:body_end] + two[body_end:].replace(
        "    bad: list[str] = []", f"    _second = {sql!r}\n    bad: list[str] = []", 1)
    assert injected != two
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.extract_runner_deps_sql(injected)


def test_an_f_string_or_concatenated_statement_raises_rather_than_matching_a_fragment(runner_text):
    sql = runner_sql(runner_text)
    as_fstring = runner_text.replace('"""' + sql + '"""', 'f"""' + sql + '"""', 1) if ('"""' + sql + '"""') in runner_text else None
    assert as_fstring is not None and as_fstring != runner_text
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.extract_runner_deps_sql(as_fstring)
    half = len(sql) // 2
    concatenated = runner_text.replace('"""' + sql + '"""', repr(sql[:half]) + " + " + repr(sql[half:]), 1)
    assert concatenated != runner_text
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.extract_runner_deps_sql(concatenated)


def test_a_truncated_statement_raises(runner_text):
    sql = runner_sql(runner_text)
    cut = sql[: sql.rindex(") f ON true")]
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.extract_runner_deps_sql(runner_text.replace(sql, cut))


def test_the_statement_in_another_function_does_not_count():
    src = ("def other(cur):\n    cur.execute('''SELECT dep.asset_id FROM x ) f ON true''')\n"
           "def deps_unsatisfied(cur, c, a):\n    return []\n")
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.extract_runner_deps_sql(src)


def test_runner_text_at_ref_raises_when_git_cannot_produce_the_file():
    def failing_git(repo, args):
        return subprocess.CompletedProcess(args, 128, "def deps_unsatisfied(): pass", "fatal: path does not exist")   # rc wins over stdout

    def empty_git(repo, args):
        return subprocess.CompletedProcess(args, 0, "  \n", "")
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.runner_text_at_ref(REPO, "HEAD", git=failing_git)
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.runner_text_at_ref(REPO, "HEAD", git=empty_git)
    with pytest.raises(slw.RunnerSqlExtractionError):
        slw.runner_text_at_ref(REPO, "no-such-ref-xyz")                       # real git, unknown ref


def test_extraction_error_is_a_level_wave_error():
    assert issubclass(slw.RunnerSqlExtractionError, slw.LevelWaveError)


def test_this_file_has_no_skip_or_xfail():
    text = pathlib.Path(__file__).read_text(encoding="utf-8")
    banned = ["pytest." + w for w in ("skip", "xfail", "importorskip")] + ["mark." + w for w in ("skip", "skipif", "xfail")]
    assert [w for w in banned if w in text.replace(" ", "")] == []
