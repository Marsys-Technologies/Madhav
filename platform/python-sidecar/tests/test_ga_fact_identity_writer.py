"""The registered writer `ga_fact_identity` (migration 1333): contract conformance + behaviour on a disposable PostgreSQL.

WHAT THIS PROVES
  Static / DB-free
    * the class is `@register('ga_fact_identity')`, a `WriterBase` subclass with a light `run(ctx)`, NOT wrapped in `l1_producer_contract`
      (that boundary is the 19 producers' data-plane generations);
    * the FROZEN-contract negatives, by AST: no commit / rollback / close / connect, no `asset_throughput`, only `ctx.db_conn`;
    * the shared body (`brahmagyan/fact_identity_index.py`) is likewise free of commit / rollback / close and uses explicit `tuple_row`
      cursors (the orchestrator connection is `dict_row`; the original script's bare `fetchone()[0]` would break there);
    * the failed-check path RAISES (the orchestrator then rolls the savepoint back), invalid config is refused, dry-run writes nothing and
      never fails on the NOT_EVALUATED clause.
  Live (disposable cluster, production-shaped roles, migration 1333 applied AS amjis_app, the writer run AS data_plane_builder on a
  `dict_row` connection exactly like the orchestrator's)
    * ROW EQUIVALENCE: for a fixture of parsed, identity-free (all 15 reasons) facts the writer's rows equal, column for column (computed_at
      excluded), the rows of the ORIGINAL standalone script body (frozen verbatim below from origin/main before this PR), and the refactored
      script's `build_index_for_chart` too;
    * IDEMPOTENT: a second run leaves the same rows; chart B (another chart) is never touched;
    * REBUILD: after a chart_facts delete-then-insert (new fact_ids, new build_id) the FK cascade empties the index and the writer repopulates it;
    * NO COMMIT: after `run()` a `rollback()` restores the prior index (the writer committed nothing);
    * FAIL-CLOSED: a gap fact, or (`exact` mode) a missing identity-free reason, raises and a savepoint rollback leaves the prior
      index untouched; `subset` mode tolerates a missing reason but never a new one.
HONEST LIMITS: not production data; the 15-reason fixture proves the exact-mode path, it does not claim any real chart satisfies it (the
first real run will say). `REQUIRE_PG_BINARIES=1` turns a missing binary from a skip into a failure.
"""
from __future__ import annotations

import ast
import inspect
import pathlib
import re
import time

import psycopg
import pytest
from psycopg.rows import dict_row

from brahmagyan.fact_identity_check import classify_fact
from pipeline.orchestrator.writers import ContextSpec, WriterBase, WriterResult, get_writer, list_writers
from tests import test_migration_1262_chart_fact_identity_registration as m
from tests.test_migration_1262_chart_fact_identity_registration import cluster  # noqa: F401  (module-scoped disposable-cluster fixture)
from tests.test_migration_1333_ga_fact_identity_writer import ASSET, BUILDER, REAL_SQL, Env1333

_SIDECAR = pathlib.Path(__file__).resolve().parents[1]
WRITER_FILE = _SIDECAR / "pipeline" / "orchestrator" / "writers" / "ga_fact_identity.py"
INDEX_FILE = _SIDECAR / "brahmagyan" / "fact_identity_index.py"
CHART_A, CHART_B = m.CHART_A, m.CHART_B
NEW_BUILD = "d4d4d4d4-d4d4-4d4d-8d4d-d4d4d4d4d4d4"

# ----------------------------------------------------------------------------------------------------------------------------
# ORIGINAL standalone G-IDX body, frozen VERBATIM from origin/main (scripts/build_fact_identity_index.py, before this PR moved it to
# brahmagyan/fact_identity_index.py). It is the reference the writer must reproduce row for row. Do not edit.
# ----------------------------------------------------------------------------------------------------------------------------
FETCH_BATCH = 20_000
INSERT_BATCH = 5_000

INSERT_SQL = """
    INSERT INTO chart_fact_identity (
        fact_id, chart_id, entity_kind, graha_code, graha_code_secondary,
        house_num, house_num_secondary, varga_id, sign_num,
        parse_rule, parsed_from, build_id, computed_at
    ) VALUES (
        %(fact_id)s, %(chart_id)s, %(entity_kind)s, %(graha_code)s, %(graha_code_secondary)s,
        %(house_num)s, %(house_num_secondary)s, %(varga_id)s, %(sign_num)s,
        %(parse_rule)s, %(parsed_from)s, %(build_id)s, now()
    )
"""


def _parsed_from(fact_subject: str, fact_key: str | None) -> str:
    return f"fact_subject={fact_subject!r};fact_key={fact_key!r}"


def build_index_for_chart(conn, chart_id: str, dry_run: bool = False) -> dict:
    """Delete-then-insert scoped to `chart_id` (§N.3). Returns a summary
    dict with the real, computed counts (§N.8 — every number here comes
    from an actual detector query / actual row count, not an estimate)."""
    import psycopg
    from psycopg.rows import tuple_row

    t0 = time.time()
    total = parsed = identity_free = gap = 0
    entity_kind_counts: dict[str, int] = {}
    identity_free_reasons: dict[str, int] = {}
    gap_examples: dict[tuple, str] = {}

    with conn.cursor(row_factory=tuple_row) as read_cur:
        read_cur.execute(
            "SELECT fact_id, fact_category, fact_subject, fact_key, build_id "
            "FROM chart_facts WHERE chart_id = %s",
            (chart_id,),
        )
        rows_to_insert = []

        with conn.cursor() as write_cur:
            if not dry_run:
                write_cur.execute(
                    "DELETE FROM chart_fact_identity WHERE chart_id = %s",
                    (chart_id,),
                )
                deleted = write_cur.rowcount
            else:
                deleted = None

            while True:
                batch = read_cur.fetchmany(FETCH_BATCH)
                if not batch:
                    break
                for fact_id, fact_category, fact_subject, fact_key, build_id in batch:
                    total += 1
                    kind, payload = classify_fact(fact_category, fact_subject, fact_key)
                    if kind == "parsed":
                        match = payload
                        parsed += 1
                        entity_kind_counts[match.entity_kind] = entity_kind_counts.get(match.entity_kind, 0) + 1
                        rows_to_insert.append({
                            "fact_id": fact_id,
                            "chart_id": chart_id,
                            "entity_kind": match.entity_kind,
                            "graha_code": match.graha_code,
                            "graha_code_secondary": match.graha_code_secondary,
                            "house_num": match.house_num,
                            "house_num_secondary": match.house_num_secondary,
                            "varga_id": match.varga_id,
                            "sign_num": match.sign_num,
                            "parse_rule": match.parse_rule,
                            "parsed_from": _parsed_from(fact_subject, fact_key),
                            "build_id": str(build_id) if build_id else None,
                        })
                        if len(rows_to_insert) >= INSERT_BATCH and not dry_run:
                            write_cur.executemany(INSERT_SQL, rows_to_insert)
                            rows_to_insert = []
                        continue

                    if kind == "identity_free":
                        identity_free += 1
                        identity_free_reasons[payload] = identity_free_reasons.get(payload, 0) + 1
                    else:  # "gap": neither parsed nor a recognised identity-free token
                        gap += 1
                        key = (fact_category, fact_key)
                        if key not in gap_examples:
                            gap_examples[key] = fact_subject

            if rows_to_insert and not dry_run:
                write_cur.executemany(INSERT_SQL, rows_to_insert)

            # The detector behind `rows == parsed`: count what is ACTUALLY in the
            # table for this chart after the insert (same transaction). Not
            # measured in a dry-run -> None (NOT_EVALUATED), never assumed.
            rows_in_table = None
            if not dry_run:
                write_cur.execute(
                    "SELECT count(*) FROM chart_fact_identity WHERE chart_id = %s",
                    (chart_id,),
                )
                rows_in_table = int(write_cur.fetchone()[0])

    denom = parsed + gap
    coverage_pct = (100.0 * parsed / denom) if denom else 100.0

    return {
        "chart_id": chart_id,
        "deleted_prior_rows": deleted,
        "total_facts": total,
        "parsed": parsed,
        "identity_free": identity_free,
        "gap": gap,
        "rows_in_table": rows_in_table,
        "coverage_of_identity_bearing_pct": round(coverage_pct, 4),
        "entity_kind_counts": entity_kind_counts,
        "identity_free_reasons": identity_free_reasons,
        "gap_examples": gap_examples,
        "elapsed_sec": round(time.time() - t0, 2),
    }


# ----------------------------------------------------------------------------------------------------------------------------
# fixtures
# ----------------------------------------------------------------------------------------------------------------------------
# one sample of every identity-free reason in the allowed set (14 + scope_cap_sentinel), keyed by the reason it must classify to
IDENTITY_FREE_SAMPLES = {
    "ashtakavarga_kakshya_index_not_house": ("ashtakavarga_bhinna", "KAKSHYA_3", "bindus"),
    "ayurdaya_method_label": ("ayurdaya", "NISARGAYU", "years"),
    "bhrigu_nadi_chakra_index_not_house": ("bhrigu_chakra", "BHRIGU_CHAKRA_4", "k"),
    "dhaiya_subperiod_label_moon_relative_not_lagna_house": ("sade_sati_dhaiya", "DHAIYA_2H_5", "k"),
    "dosha_label_catalog_label": ("dosha_label", "manglik", "k"),
    "fixed_reference_lookup_table_row_not_natal_placement": ("transit_ref", "TRANSIT_NAK_1", "k"),
    "jaimini_karaka_role_label": ("jaimini_karaka", "PITRIKARAKA", "k"),
    "nakshatra_name_fifth_dimension_out_of_scope": ("nakshatra", "Vishakha", "k"),
    "panchanga_constant_label": ("panchanga", "TITHI_BIRTH", "k"),
    "sade_sati_cycle_phase_label_moon_relative_not_lagna_house": ("sade_sati", "CYCLE_1", "k"),
    "saham_arabic_part_label": ("saham", "SAHAM_PUNYA", "k"),
    "special_point_or_aggregate_marker": ("special", "INDU_LAGNA", "k"),
    "tajik_hadda_degree_term_index_not_house": ("tajik_hadda", "HADDA_12", "k"),
    "yoga_label_catalog_label": ("yoga_label", "malavya", "k"),
    "scope_cap_sentinel": ("dasha_scope_cap", "PRANA_DASHA", "k"),
}
PARSED_SAMPLES = [
    ("graha_position", "SUN", "house_d1"), ("graha_position", "MOON", "sign"), ("graha_position", "MARS", "house_d1"),
    ("sign_fact", "Aries", "k"), ("sign_fact", "Taurus", "k"), ("varga_position", "D9.SUN", "sign"), ("varga_position", "D9.MOON", "sign"),
    ("varga_position", "D9.VEN", "sign"),
]
GAP_SAMPLE = ("graha_in_house", "SUN.H4", "k")  # classified as neither parsed nor identity-free


def _facts(chart: str, build: str, tag: str, *, reasons: bool = True, extra: list | None = None, parsed: list | None = None) -> list[tuple]:
    rows = []
    for i, (cat, subj, key) in enumerate((parsed or PARSED_SAMPLES) + (list(IDENTITY_FREE_SAMPLES.values()) if reasons else []) + (extra or [])):
        rows.append((f"{tag}-{chart[:4]}-{i}", chart, build, cat, subj, key))
    return rows


def _insert_facts(conn, rows: list[tuple]) -> None:
    for fact_id, chart, build, cat, subj, key in rows:
        conn.execute(
            "INSERT INTO public.chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key,"
            " citation_ref, citation_human, source_calculation, verification_pass_status, engine_version, computed_at)"
            " VALUES (%s,%s,'lahiri',%s,%s,%s,%s,'c','c','s','two_pass_verified','e',now())", (fact_id, chart, build, cat, subj, key))


def _reset_facts(env: Env1333, rows: list[tuple], *, identity: bool = False) -> None:
    """Replace ALL chart_facts / index rows with `rows` (admin connection; the FK cascade is part of what is under test elsewhere)."""
    with env.admin() as c:
        c.execute("DELETE FROM public.chart_facts")  # cascades into the index
        _insert_facts(c, rows)


SNAPSHOT_SQL = ("SELECT fact_id, chart_id::text, entity_kind, graha_code, graha_code_secondary, house_num, house_num_secondary, varga_id,"
                " sign_num, parse_rule, parsed_from, build_id::text FROM public.chart_fact_identity WHERE chart_id = %s ORDER BY fact_id")


def _snapshot(env: Env1333, chart: str) -> list[tuple]:
    with env.admin() as c:
        return [tuple(r) for r in c.execute(SNAPSHOT_SQL, (chart,)).fetchall()]


def _expected_from_classifier(rows: list[tuple]) -> list[tuple]:
    out = []
    for fact_id, chart, build, cat, subj, key in rows:
        kind, match = classify_fact(cat, subj, key)
        if kind == "parsed":
            out.append((fact_id, chart, match.entity_kind, match.graha_code, match.graha_code_secondary, match.house_num,
                        match.house_num_secondary, match.varga_id, match.sign_num, match.parse_rule,
                        f"fact_subject={subj!r};fact_key={key!r}", build))
    return sorted(out)


def _builder_conn(env: Env1333):
    """Like pipeline/orchestrator/db.py: a dict_row connection, autocommit off, as the build-pipeline role."""
    return env.cl.connect(env.db, BUILDER) if False else psycopg.connect(
        host=env.cl.sock, port=env.cl.port, dbname=env.db, user=BUILDER, row_factory=dict_row, connect_timeout=10)


def _ctx(conn, chart: str, **config) -> ContextSpec:
    return ContextSpec(asset_id=ASSET, build_id="e5e5e5e5-e5e5-4e5e-8e5e-e5e5e5e5e5e5", db_conn=conn, config={"chart_id": chart, **config})


def _run_writer(env: Env1333, chart: str, *, commit: bool = True, **config) -> WriterResult:
    conn = _builder_conn(env)
    try:
        res = get_writer(ASSET)().run(_ctx(conn, chart, **config))
        if commit:
            conn.commit()  # the ORCHESTRATOR commits, never the writer
        else:
            conn.rollback()
        return res
    finally:
        conn.close()


def _applied_env(cl, rows_a: list[tuple], rows_b: list[tuple] | None = None) -> Env1333:
    env = Env1333(cl)
    _reset_facts(env, rows_a + (rows_b or []))
    env.apply(REAL_SQL)  # migration 1333 as amjis_app: grants the builder INSERT + DELETE
    return env


# ----------------------------------------------------------------------------------------------------------------------------
# static / DB-free
# ----------------------------------------------------------------------------------------------------------------------------
def test_the_fixture_really_covers_every_allowed_reason_and_the_gap_sample_is_a_gap():
    from brahmagyan.fact_identity_check import IDENTITY_FREE_REASONS_ALLOWED
    got = {}
    for reason, (cat, subj, key) in IDENTITY_FREE_SAMPLES.items():
        kind, payload = classify_fact(cat, subj, key)
        assert (kind, payload) == ("identity_free", reason), (reason, kind, payload)
        got[reason] = payload
    assert set(got) == set(IDENTITY_FREE_REASONS_ALLOWED)
    assert all(classify_fact(*s)[0] == "parsed" for s in PARSED_SAMPLES)
    assert classify_fact(*GAP_SAMPLE)[0] == "gap"


def test_registered_light_writer_outside_the_producer_contract():
    cls = get_writer(ASSET)
    assert cls is not None and issubclass(cls, WriterBase) and list_writers()[ASSET] is cls
    assert cls.asset_id == ASSET
    assert "run" in cls.__dict__, "a light writer defines run(ctx)"
    assert "run_substep" not in cls.__dict__ and "plan_substeps" not in cls.__dict__
    assert not getattr(cls, "__l1_data_plane_contract__", False), "not one of the 19 data-plane producers"
    for rel in cls.source_paths:
        assert (_SIDECAR.parents[1] / rel).is_file(), rel
    from pipeline.orchestrator.asset_runner import get_writer_source_hash
    assert len(get_writer_source_hash(ASSET)) == 64


def _calls(tree: ast.AST) -> set[str]:
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", ""))
    return out


@pytest.mark.parametrize("path", [WRITER_FILE, INDEX_FILE], ids=["writer", "index_body"])
def test_frozen_contract_negatives(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = _calls(tree)
    assert not ({"commit", "rollback", "close", "connect", "set_session", "autocommit"} & calls), calls
    # no SQL string literal of the code writes the build-state table (the orchestrator is its sole writer)
    literals = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assert not any(re.search(r"(INSERT\s+INTO|UPDATE|DELETE\s+FROM)\s+asset_throughput", s) for s in literals)


def test_index_body_uses_explicit_tuple_row_cursors_only():
    tree = ast.parse(INDEX_FILE.read_text(encoding="utf-8"))
    cursors = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "cursor"]
    assert len(cursors) == 2, "the body opens exactly one read and one write cursor"
    for c in cursors:
        assert [(k.arg, getattr(k.value, "id", None)) for k in c.keywords] == [("row_factory", "tuple_row")], "every cursor must ask for tuple_row"
    src = INDEX_FILE.read_text(encoding="utf-8")
    assert "chart_facts WHERE chart_id" in src and "DELETE FROM chart_fact_identity WHERE chart_id" in src
    assert not any(w in src for w in ("INSERT INTO chart_facts", "DELETE FROM chart_facts", "UPDATE chart_facts"))


def test_the_script_and_the_writer_share_one_body():
    import importlib.util
    spec = importlib.util.spec_from_file_location("gidx_script_under_test", _SIDECAR / "scripts" / "build_fact_identity_index.py")
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    from brahmagyan import fact_identity_index as lib
    assert script.build_index_for_chart is lib.build_index_for_chart and script.INSERT_SQL == lib.INSERT_SQL


class _FakeCur:
    def __init__(self, conn): self.conn, self._rows, self.rowcount = conn, [], 0
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        if s.startswith("SELECT fact_id, fact_category"): self._rows = list(self.conn.facts)
        elif s.startswith("DELETE FROM chart_fact_identity"): self.conn.log.append("delete"); self.rowcount = len(self.conn.identity); self.conn.identity = []
        elif s.startswith("SELECT count(*) FROM chart_fact_identity"): self._rows = [(len(self.conn.identity),)]
        else: raise AssertionError(s)
    def executemany(self, sql, seq): self.conn.log.append("insert"); self.conn.identity.extend(seq)
    def fetchmany(self, n): out, self._rows = self._rows[:n], self._rows[n:]; return out
    def fetchone(self): return self._rows[0]


class _FakeConn:
    def __init__(self, facts): self.facts, self.identity, self.log = facts, [], []
    def cursor(self, **kw): self.log.append(("cursor", sorted(kw))); return _FakeCur(self)
    def commit(self): raise AssertionError("the writer must never commit")
    def rollback(self): raise AssertionError("the writer must never roll back")
    def close(self): raise AssertionError("the writer must never close")


def _fake_facts(rows):
    return [(r[0], r[3], r[4], r[5], r[2]) for r in rows]


def test_dry_run_writes_nothing_and_does_not_fail_on_the_not_evaluated_clause():
    conn = _FakeConn(_fake_facts(_facts(CHART_A, m.BUILD_A, "f")))
    res = get_writer(ASSET)().run(ContextSpec(asset_id=ASSET, build_id="b", db_conn=conn, dry_run=True,
                                              config={"chart_id": CHART_A, "fact_identity_reasons_mode": "exact"}))
    assert res.rows_inserted == 0 and "dry-run" in res.notes and "delete" not in conn.log and "insert" not in conn.log


def test_a_failed_check_raises_instead_of_returning():
    conn = _FakeConn(_fake_facts(_facts(CHART_A, m.BUILD_A, "f", extra=[GAP_SAMPLE])))
    with pytest.raises(RuntimeError, match=r"corrected G-IDX check FAILED.*gap_within_limit"):
        get_writer(ASSET)().run(_ctx(conn, CHART_A, fact_identity_reasons_mode="exact"))


def test_subset_is_the_default_exact_is_opt_in_and_an_invalid_mode_is_refused():
    conn = _FakeConn(_fake_facts(_facts(CHART_A, m.BUILD_A, "f", reasons=False)))
    res = get_writer(ASSET)().run(_ctx(conn, CHART_A))  # no mode given -> subset -> a MISSING known reason (all 15 absent here) passes
    assert res.rows_inserted == len(PARSED_SAMPLES) and "mode=subset" in res.notes
    with pytest.raises(RuntimeError, match="identity_free_reason_set"):
        get_writer(ASSET)().run(_ctx(_FakeConn(_fake_facts(_facts(CHART_A, m.BUILD_A, "f", reasons=False))), CHART_A, fact_identity_reasons_mode="exact"))
    with pytest.raises(ValueError, match="fact_identity_reasons_mode"):
        get_writer(ASSET)().run(_ctx(conn, CHART_A, fact_identity_reasons_mode="lenient"))


def test_a_chart_with_no_facts_fails_facts_present():
    with pytest.raises(RuntimeError, match="facts_present"):
        get_writer(ASSET)().run(_ctx(_FakeConn([]), CHART_A, fact_identity_reasons_mode="subset"))


# ----------------------------------------------------------------------------------------------------------------------------
# live: disposable PostgreSQL, production-shaped roles, writer run AS data_plane_builder on a dict_row connection
# ----------------------------------------------------------------------------------------------------------------------------
def test_writer_rows_equal_the_original_script_rows_and_the_classifier(cluster):
    rows_a, rows_b = _facts(CHART_A, m.BUILD_A, "f"), _facts(CHART_B, m.BUILD_B, "g")
    env = _applied_env(cluster, rows_a, rows_b)
    try:
        # reference 1: the ORIGINAL script body, run as the owner-path role, in a transaction that is rolled back
        ref = psycopg.connect(host=cluster.sock, port=cluster.port, dbname=env.db, user="amjis_app", connect_timeout=10)
        try:
            summary = build_index_for_chart(ref, CHART_A)
            ref_rows = [tuple(r) for r in ref.execute(SNAPSHOT_SQL, (CHART_A,)).fetchall()]
            ref.rollback()
        finally:
            ref.close()
        assert summary["gap"] == 0 and summary["parsed"] == len(PARSED_SAMPLES) and summary["rows_in_table"] == len(PARSED_SAMPLES)
        assert ref_rows == _expected_from_classifier(rows_a), "the frozen original body must itself equal the classifier (fixture sanity)"
        _run_writer(env, CHART_B, fact_identity_reasons_mode="exact")  # another chart's index, which chart A's run must leave alone
        before_b = _snapshot(env, CHART_B)
        assert len(before_b) == len(PARSED_SAMPLES)

        res = _run_writer(env, CHART_A, fact_identity_reasons_mode="exact")
        assert res.asset_id == ASSET and res.rows_inserted == len(PARSED_SAMPLES) and res.rows_inserted == summary["rows_in_table"]
        assert _snapshot(env, CHART_A) == ref_rows, "writer rows must equal the original standalone script's rows exactly"
        assert _snapshot(env, CHART_B) == before_b, "another chart's index must never be touched"

        # reference 2: the refactored script entry point is the same function
        import importlib.util
        spec = importlib.util.spec_from_file_location("gidx_script_live", _SIDECAR / "scripts" / "build_fact_identity_index.py")
        script = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script)
        c = psycopg.connect(host=cluster.sock, port=cluster.port, dbname=env.db, user="amjis_app", connect_timeout=10)
        try:
            script.build_index_for_chart(c, CHART_A)
            assert [tuple(r) for r in c.execute(SNAPSHOT_SQL, (CHART_A,)).fetchall()] == ref_rows
            c.rollback()
        finally:
            c.close()
    finally:
        env.drop()


def test_idempotent_second_run_and_no_accretion(cluster):
    rows_a = _facts(CHART_A, m.BUILD_A, "f")
    env = _applied_env(cluster, rows_a, _facts(CHART_B, m.BUILD_B, "g"))
    try:
        _run_writer(env, CHART_A, fact_identity_reasons_mode="exact")
        first = _snapshot(env, CHART_A)
        again = _run_writer(env, CHART_A, fact_identity_reasons_mode="exact")
        assert _snapshot(env, CHART_A) == first and again.rows_inserted == len(first)
        with env.admin() as c:
            assert c.execute("SELECT count(*) FROM public.chart_fact_identity WHERE chart_id = %s", (CHART_A,)).fetchone()[0] == len(PARSED_SAMPLES)
    finally:
        env.drop()


def test_after_a_chart_facts_rebuild_the_cascade_empties_the_index_and_the_writer_repopulates_it(cluster):
    rows_a = _facts(CHART_A, m.BUILD_A, "f")
    env = _applied_env(cluster, rows_a, _facts(CHART_B, m.BUILD_B, "g"))
    try:
        _run_writer(env, CHART_A, fact_identity_reasons_mode="exact")
        _run_writer(env, CHART_B, fact_identity_reasons_mode="exact")
        assert len(_snapshot(env, CHART_A)) == len(PARSED_SAMPLES)
        # a ga_* rebuild: delete-then-insert of the chart's facts as the BUILDER, with NEW fact_ids and a NEW build_id (the FACTID_RESTORE event)
        new_rows = _facts(CHART_A, NEW_BUILD, "n")
        b = _builder_conn(env)
        try:
            b.execute("DELETE FROM public.chart_facts WHERE chart_id = %s", (CHART_A,))
            _insert_facts(b, new_rows)
            b.commit()
        finally:
            b.close()
        assert _snapshot(env, CHART_A) == [], "the FK cascade (kept on purpose) empties the index when its facts are replaced"
        assert len(_snapshot(env, CHART_B)) == len(PARSED_SAMPLES)
        res = _run_writer(env, CHART_A, fact_identity_reasons_mode="exact")
        assert res.rows_inserted == len(PARSED_SAMPLES)
        assert _snapshot(env, CHART_A) == _expected_from_classifier(new_rows)
        assert {r[-1] for r in _snapshot(env, CHART_A)} == {NEW_BUILD}
    finally:
        env.drop()


def test_the_writer_commits_nothing_the_orchestrator_owns_the_transaction(cluster):
    rows_a = _facts(CHART_A, m.BUILD_A, "f")
    env = _applied_env(cluster, rows_a)
    try:
        _run_writer(env, CHART_A, fact_identity_reasons_mode="exact")
        committed = _snapshot(env, CHART_A)
        # stale the index by hand, then run the writer WITHOUT committing and roll back: the stale state must come back
        with env.admin() as c:
            c.execute("DELETE FROM public.chart_fact_identity WHERE chart_id = %s", (CHART_A,))
        conn = _builder_conn(env)
        try:
            get_writer(ASSET)().run(_ctx(conn, CHART_A, fact_identity_reasons_mode="exact"))
            assert conn.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS and not conn.closed
            conn.rollback()
        finally:
            conn.close()
        assert _snapshot(env, CHART_A) == [], "run() committed something"
        _run_writer(env, CHART_A, fact_identity_reasons_mode="exact")
        assert _snapshot(env, CHART_A) == committed
    finally:
        env.drop()


@pytest.mark.parametrize("variant", ["gap_fact", "exact_missing_reason"])
def test_a_failed_check_raises_and_a_savepoint_rollback_leaves_the_prior_index_untouched(cluster, variant):
    good = _facts(CHART_A, m.BUILD_A, "f")
    env = _applied_env(cluster, good)
    try:
        _run_writer(env, CHART_A, fact_identity_reasons_mode="exact")
        prior = _snapshot(env, CHART_A)
        # make the chart fail the check
        with env.admin() as c:
            if variant == "gap_fact":
                _insert_facts(c, [("gap-1", CHART_A, m.BUILD_A, *GAP_SAMPLE)])
                mode = "subset"
            else:
                c.execute("DELETE FROM public.chart_facts WHERE chart_id = %s AND fact_subject = 'PRANA_DASHA'", (CHART_A,))
                mode = "exact"
            c.execute("DELETE FROM public.chart_fact_identity WHERE chart_id = %s AND fact_id = (SELECT min(fact_id) FROM public.chart_fact_identity WHERE chart_id = %s)", (CHART_A, CHART_A))
        damaged = _snapshot(env, CHART_A)
        conn = _builder_conn(env)
        try:
            conn.execute("SAVEPOINT orchestrator_substep")  # what the orchestrator wraps around a sub-step
            with pytest.raises(RuntimeError, match="corrected G-IDX check FAILED"):
                get_writer(ASSET)().run(_ctx(conn, CHART_A, fact_identity_reasons_mode=mode))
            conn.execute("ROLLBACK TO SAVEPOINT orchestrator_substep")
            conn.commit()
        finally:
            conn.close()
        assert _snapshot(env, CHART_A) == damaged != prior, "the failed run must leave the index exactly as it found it"
    finally:
        env.drop()


def test_subset_mode_tolerates_a_missing_reason_but_never_a_new_one(cluster):
    base = _facts(CHART_A, m.BUILD_A, "f", reasons=False, extra=[IDENTITY_FREE_SAMPLES["saham_arabic_part_label"]])
    env = _applied_env(cluster, base)
    try:
        res = _run_writer(env, CHART_A, fact_identity_reasons_mode="subset")
        assert res.rows_inserted == len(PARSED_SAMPLES)
        with env.admin() as c:
            # an identity-free token whose reason is NOT in the allowed set cannot exist (classify_unparsed_subject only returns allowed or
            # the unobserved 'yoga_or_dosha_catalog_label'), so use that one: reachable in code, never observed, must fail in BOTH modes
            from brahmagyan.fact_identity_parser import KNOWN_YOGA_DOSHA_LABELS
            subj = sorted(KNOWN_YOGA_DOSHA_LABELS)[0]
            assert classify_fact("x", subj, "k") == ("identity_free", "yoga_or_dosha_catalog_label")
            _insert_facts(c, [("new-reason", CHART_A, m.BUILD_A, "x", subj, "k")])
        for cfg in ({}, {"fact_identity_reasons_mode": "subset"}, {"fact_identity_reasons_mode": "exact"}):  # {} = the default (subset)
            conn = _builder_conn(env)
            try:
                with pytest.raises(RuntimeError, match="identity_free_reason_set"):
                    get_writer(ASSET)().run(_ctx(conn, CHART_A, **cfg))
            finally:
                conn.rollback()
                conn.close()
    finally:
        env.drop()


def test_without_the_migration_the_builder_cannot_write_the_index(cluster):
    """The grant half of 1333 is load-bearing: the writer, run as the real build identity before the migration, is refused."""
    env = Env1333(cluster)
    try:
        _reset_facts(env, _facts(CHART_A, m.BUILD_A, "f"))
        conn = _builder_conn(env)
        try:
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                get_writer(ASSET)().run(_ctx(conn, CHART_A, fact_identity_reasons_mode="exact"))
        finally:
            conn.rollback()
            conn.close()
    finally:
        env.drop()


def test_reviewed_output_digest_is_content_sensitive_and_ignores_build_id_and_the_clock(cluster):
    """Migration 1333's reviewed spec, loaded through the PRODUCTION loader and run by the PRODUCTION digest function, on the canonical chart.

    A wrong spec (an unknown column, a per-rebuild column) would make `compute_output_digest` raise or drift, and the orchestrator marks the asset
    errored on a provenance-receipt failure — so this is the test that the spec is safe to ship."""
    from pipeline.orchestrator.output_digest import compute_output_digest, load_output_digest_spec

    canon = "482012f1-710e-4a25-994a-93821f5871aa"
    env = _applied_env(cluster, _facts(canon, m.BUILD_A, "c"))

    def digest() -> tuple[str, str]:
        conn = psycopg.connect(host=cluster.sock, port=cluster.port, dbname=env.db, user="amjis_app", row_factory=dict_row, connect_timeout=10)
        try:
            with conn.cursor() as cur:
                loaded = load_output_digest_spec(cur, ASSET)
                assert loaded is not None and loaded.spec["components"][0]["where_equals"] == {"chart_id": canon}
                d, sha = compute_output_digest(cur, asset_id=ASSET)
                assert sha == loaded.spec_sha256
                return d, sha
        finally:
            conn.rollback()
            conn.close()

    try:
        _run_writer(env, canon, fact_identity_reasons_mode="exact")
        d1, sha = digest()
        assert len(d1) == 64
        time.sleep(0.01)
        _run_writer(env, canon, fact_identity_reasons_mode="exact")  # computed_at moves, nothing else
        assert digest() == (d1, sha), "the digest must ignore computed_at"
        with env.admin() as c:
            c.execute("UPDATE public.chart_facts SET build_id = %s WHERE chart_id = %s", (NEW_BUILD, canon))
        _run_writer(env, canon, fact_identity_reasons_mode="exact")  # identity.build_id is now NEW_BUILD
        assert {r[-1] for r in _snapshot(env, canon)} == {NEW_BUILD}
        assert digest() == (d1, sha), "the digest must ignore build_id (a rebuild's generation id)"
        with env.admin() as c:
            c.execute("UPDATE public.chart_facts SET fact_subject = 'VEN' WHERE chart_id = %s AND fact_subject = 'SUN' AND fact_category = 'graha_position'", (canon,))
        _run_writer(env, canon, fact_identity_reasons_mode="exact")
        assert digest()[0] != d1, "the digest must change when an identity column changes"
    finally:
        env.drop()
