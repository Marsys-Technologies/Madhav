"""SR-OD1 NDH (TRIAL_READY T11) — ND-H applied IN PLACE on 1.2.0: content follows migration 1401, the changelog digests, the retained-row census.

Rulings: SR-NDH-INPLACE (a) retained rows derived from pre-change 1.2.0 content are found and not left; (b) the 1.2.0 row carries a changelog entry — ruling ids, date,
the eight classes, content digest before and after; content follows SR-DOCTRINE-H and migration 1401. Tool under test: `scripts/kala_gochara_cutover/od1_ndh_in_place.py`.

Every database claim runs on a throwaway database built from the REAL migrations (the AM-5 chain, migration 250 for L0, then migration 1401 verbatim) on the disposable
cluster (`GOCHARA_A53_ADMIN_DSN`); NOT_RUN when it is unreachable, a failure under `GOCHARA_A53_REQUIRE_DB=1`.

Distinct claims, each with its single planted reversion (the test that fails is named):
  N1  the content the 1.2.0 rows consume from L0 IS the 1401 / BPHS content: the post-1401 database holds BPHS 47.34-39 (Rāhu mūlatrikoṇa Gemini, own Aquarius; Ketu
      mūlatrikoṇa Sagittarius, own Scorpio) and the 3.55 translator note's relations for every node pair, and its L0 digests equal the committed-seed digests
                                                                                  test_n1_*   (revert: a seed own sign changed, or the seeds not corrected → digests differ from the database's)
  N2  the PRE-change basis the changelog's "before" digest is taken over is the migration-250 database, byte for byte (not a typed approximation)
                                                                                  test_n2_*   (revert: `PRE_1401_PAIRS` altered → "before" ≠ the 250-only database)
  N3  the changelog: exact ruling ids, date, the eight classes, before ≠ after, both recomputed from independent inputs (the databases), and the committed record
      equals the recomputation — an edit of the 1.2.0 content that leaves the record stale fails                    test_n3_*   (revert: `after_soft_factors` reads the 1.0.0 row → digest moves, record stale)
  N4  registry census: a stored 1.2.0 row that is not the declared catalogue's (a pre-V1 soft-factor membership) is STALE and named; the production reader refuses it
                                                                                  test_n4_*   (revert: the registry comparison removed → CLEAN; or the reader's whole-set comparison removed → no refusal)
  N5  generation census: a generation holding 1.2.0 rows whose stored input vector recorded pre-change L0 is STALE and its rows are listed with counts and ids
                                                                                  test_n5_*   (revert: the digest comparison removed → CLEAN)
  N6  a generation that cannot be classified (no stored vector / no recorded L0 digest) is UNDETERMINED, never CLEAN       test_n6_*   (revert: unclassifiable treated as clean)
  N7  the clean database reads CLEAN, and the registry's `db_sql` part (the same detector rendered as SQL) reads t on it, f on the stale ones
                                                                                  test_n7_*   (revert: the SQL's digest literals not the post-1401 ones → reads t on the stale generation)
"""
from __future__ import annotations

import importlib.util
import json
import os
import uuid
from pathlib import Path

import pytest

from services.gochara_kernel import rule_registry as rr
from services.gochara_rules import registry as reg

from .test_a53_inventory import ADMIN_DSN, create_am5_database, drop_am5_database  # noqa: F401  (the disposable-cluster helpers)

_TOOL = Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover" / "od1_ndh_in_place.py"
_MIGRATIONS = Path(__file__).resolve().parents[4] / "migrations"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
V = "1.2.0"


def _load_tool():
    spec = importlib.util.spec_from_file_location("od1_ndh_in_place", _TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tool = _load_tool()

# ── the doctrine, typed from the served texts (independent of the seeds) ────────────────────────────────────────────────────────
#: BPHS ch.47 (bphs:PG573:C2 - bphs:PG574:C1): "The Moola trikonas of Rahu and Ketu are Gemini and Sagittarius respectively. The own signs of Rahu and Ketu are
#: Aquarius and Scorpio in that order."
BPHS47 = {"Rahu": ("Gemini", ["Aquarius"]), "Ketu": ("Sagittarius", ["Scorpio"])}
#: BPHS 3.55 translator note (bphs:PG40:C1): "Rahu: The Sun, Moon and Mars are his enemies. Jupiter, Venus and Saturn are his friends. Mercury is his neutral.
#: Ketu: The luminaries are his enemies. Mars, Venus and Saturn are his friends, while Mercury and Jupiter are his neutrals."
BPHS355 = {
    "Rahu": {"Sun": "enemy", "Moon": "enemy", "Mars": "enemy", "Jupiter": "friend", "Venus": "friend", "Saturn": "friend", "Mercury": "neutral"},
    "Ketu": {"Sun": "enemy", "Moon": "enemy", "Mars": "friend", "Venus": "friend", "Saturn": "friend", "Mercury": "neutral", "Jupiter": "neutral"},
}


# ── the throwaway database ──────────────────────────────────────────────────────────────────────────────────────────────────────

def _apply(conn, name: str) -> None:
    conn.execute((_MIGRATIONS / name).read_text(encoding="utf-8"))
    conn.execute("INSERT INTO public._migrations_applied(filename) VALUES (%s) ON CONFLICT DO NOTHING", (name,))


def _fresh(tag: str):
    import psycopg
    admin, name, dsn = create_am5_database(tag)
    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
    return admin, name, conn


@pytest.fixture(scope="module")
def pre_db():
    """AM-5 chain + the registry seeded under the FINAL profile + migration 250 only (L0 as it was before SR-DOCTRINE-H)."""
    admin, name, conn = _fresh("ndhpre")
    try:
        _apply(conn, "250_bg_dignity_reference.sql")
        with rr.rule_profile(final_rules=True):
            rr.RuleRegistryStore(conn).seed()
        yield conn
    finally:
        conn.close()
        drop_am5_database(admin, name)


@pytest.fixture(scope="module")
def post_db():
    """The same, then migration 1401 verbatim on top."""
    admin, name, conn = _fresh("ndhpost")
    try:
        _apply(conn, "250_bg_dignity_reference.sql")
        _apply(conn, "1401_l0_node_dignity_friendship.sql")
        with rr.rule_profile(final_rules=True):
            rr.RuleRegistryStore(conn).seed()
        yield conn
    finally:
        conn.close()
        drop_am5_database(admin, name)


def _l0_rows(conn):
    dig = [dict(zip(("graha", "exaltation_sign", "debilitation_sign", "moolatrikona_sign", "moolatrikona_from", "moolatrikona_to", "own_signs"), r)) for r in conn.execute(
        "SELECT graha, exaltation_sign, debilitation_sign, moolatrikona_sign, moolatrikona_from, moolatrikona_to, own_signs FROM public.bg_dignity_reference").fetchall()]
    fr = [tuple(r) for r in conn.execute("SELECT graha, other_graha, relation FROM public.bg_graha_naisargika_friendship").fetchall()]
    return dig, fr


def _plant_generation(conn, generation: str, l0: dict | None, *, vector: bool = True, path: str = "P1") -> None:
    """One generation holding ONE 1.2.0 search-path pin and (optionally) the input snapshot that records `l0`. Replica role: the foreign keys and the insert-only guards
    belong to the migrations under test elsewhere; this plants the row shapes the census reads."""
    conn.execute("SET session_replication_role = replica")
    try:
        conn.execute("INSERT INTO public.charts(id) VALUES (%s) ON CONFLICT DO NOTHING", (CHART,))
        if vector:
            vec = {"l0": l0} if l0 is not None else {"registry": {}}
            conn.execute(
                "INSERT INTO public.ka_gochara_search_input_snapshot (chart_id, generation, convention_id, input_generation_vector, consumed_fact_ids,"
                " consumed_dasha_row_ids, av_declarations, l1_facts_digest, dasha_digest, input_digest) VALUES (%s, %s, 'c', %s::jsonb, '{}', '{}', '{}', %s, %s, %s)",
                (CHART, generation, json.dumps(vec), "a" * 64, "b" * 64, uuid.uuid4().hex * 2))
        conn.execute(
            "INSERT INTO public.ka_gochara_search_path_pin (chart_id, generation, event_class, path_id, rule_version, disposition, basis, committed_ob_ids)"
            " VALUES (%s, %s, 'marriage', %s, %s, 'computed_empty', 'oracle:planted', '{}')", (CHART, generation, path, V))
    finally:
        conn.execute("SET session_replication_role = DEFAULT")


def _unplant(conn) -> None:
    conn.execute("SET session_replication_role = replica")
    try:
        for t in ("ka_gochara_search_path_pin", "ka_gochara_search_input_snapshot"):
            conn.execute(f"DELETE FROM public.{t}")
        conn.execute("DELETE FROM public.ka_gochara_rule_path_soft_factor WHERE factor_id = 'maitri_compound' AND rule_version = %s", (V,))
    finally:
        conn.execute("SET session_replication_role = DEFAULT")


@pytest.fixture()
def clean_slate(post_db):
    _unplant(post_db)
    yield post_db
    _unplant(post_db)


# ── N1 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_n1_the_post_1401_database_holds_the_bphs_content_and_the_seeds_digest_equals_it(post_db):
    dig, fr = _l0_rows(post_db)
    by = {r["graha"]: r for r in dig}
    for node, (mt, own) in BPHS47.items():
        assert (by[node]["moolatrikona_sign"], by[node]["own_signs"]) == (mt, own), node
        assert by[node]["moolatrikona_from"] is None and by[node]["moolatrikona_to"] is None, f"{node}: the verse gives signs only, no degree range"
    rel = {(a, b): r for a, b, r in fr}
    for node, table in BPHS355.items():
        for other, want in table.items():
            assert rel[(node, other)] == want, f"{node} -> {other}: the translator note says {want}"
    # the digests the INPUT VECTOR stores (p1_operands content_digest) over the database's rows == over the committed seeds the writer rebuilds L0 from
    assert tool.l0_digests(dig, fr) == tool.expected_l0_after()
    assert tool._l0_state(post_db)["state"] == "post_1401"


# ── N2 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_n2_the_before_basis_is_the_migration_250_database_byte_for_byte(pre_db):
    dig, fr = _l0_rows(pre_db)
    assert {r["graha"]: (r["moolatrikona_sign"], r["own_signs"]) for r in dig if r["graha"] in ("Rahu", "Ketu")} == {"Rahu": (None, []), "Ketu": (None, [])}
    assert tool.l0_digests(dig, fr) == tool.expected_l0_before()
    assert tool.expected_l0_before() != tool.expected_l0_after()
    assert tool._l0_state(pre_db)["state"] == "pre_1401"


# ── N3 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_n3_the_changelog_names_the_rulings_date_and_classes_and_its_digests_are_recomputed_from_independent_inputs(pre_db, post_db):
    entry = tool.changelog_entry()
    assert entry["rulings"] == ["SR-DOCTRINE-H", "SR-NDH-INPLACE"] and entry["date"] == "2026-10-22" and entry["rule_version"] == V
    assert entry["classes_changed"] == sorted(reg.ND_H_CLASSES) and len(entry["classes_changed"]) == 8
    assert entry["content_digest_before"] != entry["content_digest_after"]
    assert entry["changed"] == {"soft_factors": True, "l0_node_inputs": True, "h_table": False}      # the H table did not move: only what 1401 and V1 moved
    # recomputed over the L0 rows READ FROM THE TWO DATABASES (migration 250 / 250+1401) and the soft factors READ FROM THE SEEDED REGISTRY TABLE
    stored = {}
    for pid, fid, fver in post_db.execute("SELECT path_id, factor_id, factor_rule_version FROM public.ka_gochara_rule_path_soft_factor WHERE rule_version = %s", (V,)).fetchall():
        stored.setdefault(pid, []).append([fid, fver])
    stored = {p: sorted(v) for p, v in stored.items()}
    after_soft = {p: sorted(v) for p, v in tool.after_soft_factors().items()}
    assert stored == after_soft, "the 'after' soft factors are what the registry actually stores"
    dig_b, fr_b = _l0_rows(pre_db)
    dig_a, fr_a = _l0_rows(post_db)
    before = tool.content_digest(tool.content_bundle(soft_factors=tool.before_soft_factors(), dignity_rows=dig_b, friendship_rows=fr_b))
    after = tool.content_digest(tool.content_bundle(soft_factors=tool.after_soft_factors(), dignity_rows=dig_a, friendship_rows=fr_a))
    assert (before, after) == (entry["content_digest_before"], entry["content_digest_after"])
    # the 1.2.0 before-soft-factors are the pre-V1 rows: the bound 1.0.0 set + karaka_agent@1.2.0 (nothing at 1.3.0)
    assert all(ref[1] != reg.DOCTRINE_VERSION for refs in tool.before_soft_factors().values() for ref in refs)
    assert any(ref[1] == reg.DOCTRINE_VERSION for refs in tool.after_soft_factors().values() for ref in refs)


def test_n3_the_committed_record_equals_the_recomputation():
    """A later edit of the 1.2.0 content moves the digest; this fails until the entry is regenerated (`changelog --write`), so the record cannot go stale unseen."""
    assert tool.CHANGELOG_PATH.is_file(), "od1_ndh_changelog_1_2_0.json is not committed"
    assert tool.CHANGELOG_PATH.read_text(encoding="utf-8") == tool.render_changelog()


# ── N4 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_n4_a_pre_v1_soft_factor_row_at_1_2_0_is_stale_and_named_and_the_production_reader_refuses_it(clean_slate):
    conn = clean_slate
    assert tool.census(conn)["registry"]["stale"] == []
    with rr.rule_profile(final_rules=True):                          # the declared membership is read without complaint
        assert sorted(r["factor_id"] for r in rr.RuleRegistryStore(conn).bound_factor_rows("P1", V)) == sorted(f for f, _v in reg.RULE_PATHS[("P1", V)]["soft_factors"])
    conn.execute("SET session_replication_role = replica")           # the table is insert-only (1154): a pre-change row can only exist from before the change
    try:
        conn.execute("INSERT INTO public.ka_gochara_rule_path_soft_factor(path_id, rule_version, factor_id, factor_rule_version) VALUES ('P1', %s, 'maitri_compound', '1.0.0')", (V,))
    finally:
        conn.execute("SET session_replication_role = DEFAULT")
    out = tool.census(conn)
    assert out["verdict"] == "STALE"
    assert out["registry"]["stale"] == [["ka_gochara_rule_path_soft_factor", ["P1", V, "maitri_compound", "1.0.0"]]]
    # the consumer REFUSES the old membership (maitri_compound@1.0.0 is a bound factor, so the per-member check alone would have let it through)
    with rr.rule_profile(final_rules=True), pytest.raises(rr.RegistryDivergenceError, match="is not the declared one"):
        rr.RuleRegistryStore(conn).bound_factor_rows("P1", V)


# ── N5 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_n5_a_generation_built_on_pre_1401_l0_is_stale_with_its_rows_listed_and_a_post_1401_one_is_not(clean_slate):
    conn = clean_slate
    _plant_generation(conn, "5.0", tool.expected_l0_before())
    _plant_generation(conn, "5.1", tool.expected_l0_after())
    out = tool.census(conn, ids=True)
    assert out["verdict"] == "STALE"
    assert out["stale_generations"] == [[CHART, "5.0", "l0_differs_from_post_1401"]]          # 5.1 (post-1401) is not listed
    pins = out["retained"]["ka_gochara_search_path_pin"]
    assert pins["count"] == 2 and sorted(pins["ids"]) == [f"{CHART}/5.0/marriage/P1", f"{CHART}/5.1/marriage/P1"]
    assert out["retained"]["ka_gochara_relationship_record"]["count"] == 0 and out["registry"]["stale"] == []


# ── N6 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_n6_a_generation_that_cannot_be_classified_is_undetermined_not_clean(clean_slate):
    conn = clean_slate
    _plant_generation(conn, "5.0", None, vector=False)                                         # no stored vector at all
    _plant_generation(conn, "5.2", None, vector=True)                                          # a vector without the l0 digests
    out = tool.census(conn)
    assert out["verdict"] == "UNDETERMINED"
    assert sorted(out["undetermined_generations"]) == [[CHART, "5.0", "no_input_vector"], [CHART, "5.2", "no_l0_digest_recorded"]] and out["stale_generations"] == []


# ── N7 ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _t11_sql() -> str:
    (sql_part,) = [p for p in tool.t11_parts() if p["kind"] == "db_sql"]
    assert sql_part["expect"] == "t" and sql_part["dsn_env"] == "TRIAL_READY_LANE_DSN"
    return sql_part["sql"]


def test_n7_the_clean_database_reads_clean_and_the_registry_sql_part_reads_t_only_there(clean_slate):
    conn = clean_slate
    sql = _t11_sql()
    _plant_generation(conn, "5.1", tool.expected_l0_after())
    out = tool.census(conn)
    assert out["verdict"] == "CLEAN" and out["stale_generations"] == [] and out["undetermined_generations"] == []
    assert out["retained"]["ka_gochara_search_path_pin"]["count"] == 1 and out["l0"]["state"] == "post_1401"
    assert conn.execute(sql).fetchone()[0] is True
    _plant_generation(conn, "5.0", tool.expected_l0_before())
    assert tool.census(conn)["verdict"] == "STALE" and conn.execute(sql).fetchone()[0] is False
    _unplant(conn)
    _plant_generation(conn, "5.0", None, vector=False)
    assert tool.census(conn)["verdict"] == "UNDETERMINED" and conn.execute(sql).fetchone()[0] is False      # unclassifiable is not green


def test_n7_the_oracle_file_the_registry_part_names_is_this_file():
    (pytest_part,) = [p for p in tool.t11_parts() if p["kind"] == "pytest"]
    assert (Path(__file__).resolve().parents[3] / pytest_part["tests"][0]).samefile(__file__)


def test_n7_a_database_with_no_gochara_table_is_not_clean():
    """The detector must have something to read: an empty database reads UNDETERMINED (the cockpit's `ky_lane_head` before it is built), never CLEAN."""
    import psycopg
    admin, name, dsn = None, None, None
    try:
        admin, name, dsn = create_am5_database("ndhempty")
        with psycopg.connect(dsn, autocommit=True, connect_timeout=3) as c:
            for t in tool.ALL_RETAINED + tool.REGISTRY_TABLES + ("ka_gochara_search_input_snapshot",):
                c.execute(f"DROP TABLE IF EXISTS public.{t} CASCADE")
            out = tool.census(c)
        assert out["no_gochara_tables"] is True and out["verdict"] == "UNDETERMINED"
    finally:
        if admin is not None:
            drop_am5_database(admin, name)


def test_n8_the_census_never_connects_to_a_non_loopback_database(monkeypatch):
    """Nothing touches production (job header, Databases rule; R-2026-10-15-01): `census --dsn` refuses any host that is not loopback BEFORE a connection is attempted.
    (revert: the `_loopback_connect` host refusal removed → `psycopg.connect` is reached, which this test fails on)"""
    import psycopg

    def _no_connection(*args, **kwargs):
        raise AssertionError(f"a connection was attempted: {args!r}")

    monkeypatch.setattr(psycopg, "connect", _no_connection)
    for dsn in ("postgresql://u@db.example.invalid/x", "postgresql://u@127.0.0.1,db.example.invalid/x", "postgresql://u@10.0.0.5/x"):
        with pytest.raises(SystemExit) as exc:
            tool.main(["census", "--dsn", dsn])
        assert "refused" in str(exc.value)
