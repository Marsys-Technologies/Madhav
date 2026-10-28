"""bg_rule_book (Rule Book engine E2) — DB tests against a DISPOSABLE local Postgres.

Set RULEBOOK_E2_ADMIN_DSN to an admin DSN on a loopback-only throwaway cluster
(validated by tests/l3/_disposable_db_guard.py). Each test module run CREATEs a
uniquely named database, applies a minimal asset_registry stub plus migration
1413, and DROPs it at the end. Skipped (NOT_RUN) when the DSN is absent;
RULEBOOK_E2_REQUIRE_DB=1 turns the skip into a failure.

Covers: migration applies (and re-applies) cleanly; writer idempotency;
frozen-version refusal by writer AND by trigger; licence refusal writes
nothing; one current version; count_sql correctness; quarantined cards stored
with a reason, never active; CHECK ties of extracted columns.
"""
from __future__ import annotations

import os
import uuid
from pathlib import Path

import pytest

psycopg = pytest.importorskip("psycopg")

from brahmagyan import l0_rule_book as RB  # noqa: E402
from pipeline.orchestrator.writers import ContextSpec  # noqa: E402
from pipeline.orchestrator.writers.bg_rule_book import RuleBookWriter  # noqa: E402
from services.rulebook import schema as rb_schema  # noqa: E402
from services.rulebook.compiler import sha256_hex  # noqa: E402
from tests.l3._disposable_db_guard import assert_disposable_connection, validate_disposable_dsn  # noqa: E402
from tests.rulebook import _cards as K  # noqa: E402
from tests.rulebook._rule_book_versions import fixture_cards, write_version  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
MIGRATION = REPO / "platform" / "migrations" / "1413_bg_rule_book_l0_store.sql"

# Minimal stand-in for production asset_registry: exactly the 28 seed-upsert columns.
ASSET_REGISTRY_STUB = """
CREATE TABLE asset_registry (
  asset_id TEXT PRIMARY KEY, layer TEXT, sort_order INT, sanskrit_name TEXT, english_name TEXT,
  english_description TEXT, storage_type TEXT, target_table TEXT, count_sql TEXT, size_sql TEXT,
  target_floor INT, expected_volume_formula TEXT, expected_volume_inputs JSONB, volume_explanation TEXT,
  depends_on TEXT[], scope TEXT, is_active BOOLEAN, estimated_seconds INT, asset_type TEXT, layer_name TEXT,
  layer_index TEXT, provides_apis TEXT[], health_probe TEXT, catalog_status TEXT, asset_kind TEXT,
  has_writer BOOLEAN, has_substeps BOOLEAN, writer_timeout_seconds INT)
"""

FROZEN = "object_not_in_prerequisite_state"


def _apply_migration(conn) -> None:
    """migrate.ts shape: one transaction around the file."""
    with conn.transaction():
        conn.execute(MIGRATION.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def db_dsn():
    admin = os.environ.get("RULEBOOK_E2_ADMIN_DSN")
    if not admin:
        if os.environ.get("RULEBOOK_E2_REQUIRE_DB") == "1":
            pytest.fail("RULEBOOK_E2_REQUIRE_DB=1 but RULEBOOK_E2_ADMIN_DSN is absent")
        pytest.skip("NOT_RUN: RULEBOOK_E2_ADMIN_DSN is absent")
    validate_disposable_dsn(admin, None)
    name = f"rulebook_e2_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(admin, autocommit=True, connect_timeout=3) as a:
        a.execute(f'CREATE DATABASE "{name}"')
        # the build identity exists before the migration, as in production, so 1413 grants it and post-checks the ACL
        if not a.execute("SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder'").fetchone():
            a.execute("CREATE ROLE data_plane_builder NOLOGIN")
    info = psycopg.conninfo.conninfo_to_dict(admin)
    info["dbname"] = name
    dsn = psycopg.conninfo.make_conninfo(**info)
    with psycopg.connect(dsn) as c:
        assert_disposable_connection(c, name)
        c.execute(ASSET_REGISTRY_STUB)
        c.commit()
        _apply_migration(c)
    try:
        yield dsn
    finally:
        with psycopg.connect(admin, autocommit=True, connect_timeout=3) as a:
            a.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture()
def conn(db_dsn):
    c = psycopg.connect(db_dsn)
    try:
        yield c
    finally:
        c.rollback()
        c.close()


@pytest.fixture()
def clean(conn):
    """Every test starts from empty rule-book tables (no frozen version may survive a test)."""
    def _wipe():
        with conn.transaction():
            conn.execute("ALTER TABLE l0_rule_book_versions DISABLE TRIGGER USER")
            conn.execute("ALTER TABLE l0_rule_book_cards DISABLE TRIGGER USER")
            conn.execute("ALTER TABLE l0_rule_book_card_classes DISABLE TRIGGER USER")
            conn.execute("DELETE FROM l0_rule_book_card_classes")
            conn.execute("DELETE FROM l0_rule_book_cards")
            conn.execute("DELETE FROM l0_rule_book_versions")
            conn.execute("ALTER TABLE l0_rule_book_versions ENABLE TRIGGER USER")
            conn.execute("ALTER TABLE l0_rule_book_cards ENABLE TRIGGER USER")
            conn.execute("ALTER TABLE l0_rule_book_card_classes ENABLE TRIGGER USER")
    _wipe()
    yield conn
    conn.rollback()
    _wipe()


def _ctx(conn, manifest: Path, **cfg) -> ContextSpec:
    return ContextSpec(asset_id="bg_rule_book", build_id=f"test-{uuid.uuid4().hex[:6]}", db_conn=conn,
                       config={"rule_book_manifest": str(manifest), **cfg})


def _run(conn, manifest: Path, **cfg):
    res = RuleBookWriter().run(_ctx(conn, manifest, **cfg))
    # the writer never commits: its rows are still in the open transaction
    assert conn.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS
    conn.commit()
    return res


def _freeze(conn, version: str) -> None:
    conn.execute("UPDATE l0_rule_book_versions SET frozen_at = now() WHERE rulebook_version = %s", (version,))
    conn.commit()


def _count_sql(conn) -> int:
    sql = conn.execute("SELECT count_sql FROM asset_registry WHERE asset_id = 'bg_rule_book'").fetchone()[0]
    return conn.execute(sql).fetchone()[0]


def _pd_cards():
    """Synthetic _cards.py cards on the public-domain text id (invented prose), all compile active."""
    out = []
    for make in (K.natal_card, K.dasha_card):
        c = make()
        c["field1_citation"].update(text_id="sarvartha_chintamani", chunk_id="sarvartha_chintamani_pg9001_c01",
                                    passage_ids=["sarvartha_chintamani_pg9001_c01:en:p001"])
        out.append(c)
    return out


def _expect_frozen(conn, sql, params=()):
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState, match="l0_rule_book"):
        conn.execute(sql, params)
    conn.rollback()


# ── migration ────────────────────────────────────────────────────────────────
def test_migration_applied_and_reapplies_cleanly(conn):
    for t in ("l0_rule_book_versions", "l0_rule_book_cards", "l0_rule_book_card_classes"):
        assert conn.execute("SELECT to_regclass(%s)", (t,)).fetchone()[0] is not None
    row = conn.execute("SELECT has_writer, is_active, scope, layer_index FROM asset_registry WHERE asset_id='bg_rule_book'").fetchone()
    assert row == (True, False, "global", "L0")
    _apply_migration(conn)  # idempotent: IF NOT EXISTS / OR REPLACE / ON CONFLICT DO NOTHING
    assert conn.execute("SELECT COUNT(*) FROM asset_registry WHERE asset_id='bg_rule_book'").fetchone()[0] == 1
    n_trig = conn.execute(
        "SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE 'l0rb%' AND NOT tgisinternal").fetchone()[0]
    assert n_trig == 6


def test_builder_role_granted_dml_only(conn):
    for t in ("l0_rule_book_versions", "l0_rule_book_cards", "l0_rule_book_card_classes"):
        for priv, held in (("SELECT", True), ("INSERT", True), ("UPDATE", True), ("DELETE", True),
                           ("TRUNCATE", False), ("TRIGGER", False), ("REFERENCES", False)):
            assert conn.execute("SELECT has_table_privilege('data_plane_builder', %s, %s)", (t, priv)).fetchone()[0] is held, (t, priv)


# ── writer: rows, idempotency, ties ──────────────────────────────────────────
def test_writer_fixture_rows_and_idempotency(clean):
    conn = clean
    r1 = _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    assert (r1.rows_inserted, r1.rows_updated) == (6, 0)
    snap1 = conn.execute(
        "SELECT card_id, card_sha256, ir_sha256, status, quarantine_reason FROM l0_rule_book_cards ORDER BY card_id").fetchall()
    classes1 = conn.execute("SELECT * FROM l0_rule_book_card_classes ORDER BY 1,2,3").fetchall()
    r2 = _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    assert (r2.rows_inserted, r2.rows_updated) == (0, 6)
    assert conn.execute(
        "SELECT card_id, card_sha256, ir_sha256, status, quarantine_reason FROM l0_rule_book_cards ORDER BY card_id").fetchall() == snap1
    assert conn.execute("SELECT * FROM l0_rule_book_card_classes ORDER BY 1,2,3").fetchall() == classes1
    assert conn.execute("SELECT COUNT(*) FROM l0_rule_book_versions").fetchone()[0] == 1


def test_writer_runs_as_build_identity_and_trigger_binds_it(clean):
    """The writer works as data_plane_builder (non-owner); that role cannot switch the freeze guard off."""
    conn = clean
    conn.execute("GRANT USAGE ON SCHEMA public TO data_plane_builder")
    conn.commit()
    conn.execute("SET ROLE data_plane_builder")
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    conn.execute("RESET ROLE")
    _freeze(conn, "FIXTURE-0.1")
    conn.execute("SET ROLE data_plane_builder")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        conn.execute("ALTER TABLE l0_rule_book_cards DISABLE TRIGGER l0rbc_guard")
    conn.rollback()
    conn.execute("SET ROLE data_plane_builder")
    _expect_frozen(conn, "DELETE FROM l0_rule_book_cards")
    conn.execute("RESET ROLE")
    conn.commit()


def test_freeze_refused_outside_read_committed(clean):
    conn = clean
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    conn.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
    _expect_frozen(conn, "UPDATE l0_rule_book_versions SET frozen_at = now()")
    _freeze(conn, "FIXTURE-0.1")  # the same freeze at READ COMMITTED succeeds
    assert conn.execute("SELECT frozen_at IS NOT NULL FROM l0_rule_book_versions").fetchone()[0]


def test_stored_columns_are_the_cards_own(clean):
    """The ties Postgres cannot express: hashes over the Python canonical form, and class rows."""
    conn = clean
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    rows = conn.execute(
        "SELECT card_id, card_json, card_sha256, ir_json, ir_sha256, verdict, provenance FROM l0_rule_book_cards").fetchall()
    assert len(rows) == 6
    for cid, card, csha, ir, isha, verdict, prov in rows:
        assert sha256_hex(card) == csha, cid
        assert (ir is None and isha is None) or sha256_hex(ir) == isha, cid
        assert verdict == {"verse_cited": "scored", "commentarial_practice": "testimony"}[prov]
        got = [r[0] for r in conn.execute(
            "SELECT class_group FROM l0_rule_book_card_classes WHERE card_id = %s ORDER BY 1", (cid,)).fetchall()]
        assert got == sorted(rb_schema.class_groups(card)), cid
    v = conn.execute("SELECT manifest_sha256, card_count FROM l0_rule_book_versions").fetchone()
    src = RB.load_source(RB.FIXTURE_MANIFEST, allow_fixture=True)
    assert v == (src.manifest_sha256, 6)


def test_rerun_drops_cards_removed_from_unfrozen_version(clean, tmp_path):
    conn = clean
    cards = _pd_cards()
    _run(conn, write_version(tmp_path / "a", "TEST-DROP", cards))
    r = _run(conn, write_version(tmp_path / "b", "TEST-DROP", cards[:1]))
    assert "1 dropped" in r.notes
    assert conn.execute("SELECT COUNT(*) FROM l0_rule_book_cards WHERE rulebook_version='TEST-DROP'").fetchone()[0] == 1


# ── quarantine ───────────────────────────────────────────────────────────────
def test_quarantined_cards_stored_with_reason_never_active(clean):
    conn = clean
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    q = dict(conn.execute(
        "SELECT card_id, quarantine_reason FROM l0_rule_book_cards WHERE status='quarantined_not_evaluable'").fetchall())
    assert set(q) == {"FIX-QUAR-MEAN-1", "FIX-REDACTED-1"}
    assert all(reason and reason.strip() for reason in q.values())
    # promoting a quarantined card to active is refused by CHECK: its IR is absent or not active
    for cid in q:
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute("UPDATE l0_rule_book_cards SET status='active', quarantine_reason=NULL WHERE card_id=%s", (cid,))
        conn.rollback()
    # an active row without IR, or without a reason when non-active, is refused
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("UPDATE l0_rule_book_cards SET quarantine_reason=NULL WHERE card_id='FIX-QUAR-MEAN-1'")
    conn.rollback()


def test_status_change_allowed_while_unfrozen(clean):
    conn = clean
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    conn.execute("UPDATE l0_rule_book_cards SET status='withdrawn', quarantine_reason='withdrawn: test' WHERE card_id='FIX-NATAL-1'")
    conn.commit()
    assert conn.execute("SELECT status FROM l0_rule_book_cards WHERE card_id='FIX-NATAL-1'").fetchone()[0] == "withdrawn"


def test_check_ties_extracted_columns_to_card_json(clean):
    conn = clean
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    for sql in (
        "UPDATE l0_rule_book_cards SET category='transit' WHERE card_id='FIX-NATAL-1'",
        "UPDATE l0_rule_book_cards SET polarity='obstructive' WHERE card_id='FIX-NATAL-1'",
        "UPDATE l0_rule_book_cards SET passage_ids='{x}' WHERE card_id='FIX-NATAL-1'",
        "UPDATE l0_rule_book_cards SET verdict='testimony' WHERE card_id='FIX-NATAL-1'",
        "UPDATE l0_rule_book_cards SET card_id='OTHER' WHERE card_id='FIX-NATAL-1'",
        "UPDATE l0_rule_book_cards SET ratification_sha256=repeat('0',64) WHERE card_id='FIX-NATAL-1'",
        "UPDATE l0_rule_book_cards SET ir_sha256=NULL WHERE card_id='FIX-NATAL-1'",
        # a MISSING key must fail the CHECK, not pass as NULL
        "UPDATE l0_rule_book_cards SET card_json = card_json - 'polarity' WHERE card_id='FIX-NATAL-1'",
        "UPDATE l0_rule_book_cards SET ir_json = ir_json - 'status' WHERE card_id='FIX-NATAL-1'",
        "UPDATE l0_rule_book_cards SET ir_json = ir_json - 'card_id' WHERE card_id='FIX-NATAL-1'",
    ):
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(sql)
        conn.rollback()
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("INSERT INTO l0_rule_book_card_classes VALUES ('FIXTURE-0.1','FIX-NATAL-1','not_a_class')")
    conn.rollback()


# ── licence ──────────────────────────────────────────────────────────────────
def test_licence_refusal_writes_nothing(clean, tmp_path):
    conn = clean
    cards = fixture_cards()
    cards[0]["field1_citation"].update(text_id="bphs", passage_ids=["bphs_pg9001_c01:en:p001"])
    path = write_version(tmp_path, "TEST-LIC", cards, redact=False)
    with pytest.raises(RB.RuleBookLicenceRefused):
        RuleBookWriter().run(_ctx(conn, path))
    conn.rollback()
    assert conn.execute("SELECT COUNT(*) FROM l0_rule_book_versions").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM l0_rule_book_cards").fetchone()[0] == 0


# ── freeze: writer refusal and trigger refusal ───────────────────────────────
def test_frozen_version_refused_by_writer(clean):
    conn = clean
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    _freeze(conn, "FIXTURE-0.1")
    with pytest.raises(RB.RuleBookFrozenError, match="frozen"):
        RuleBookWriter().run(_ctx(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True))
    conn.rollback()


def test_frozen_version_refused_by_trigger(clean):
    conn = clean
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    _freeze(conn, "FIXTURE-0.1")
    _expect_frozen(conn, "UPDATE l0_rule_book_cards SET status='withdrawn', quarantine_reason='x' WHERE card_id='FIX-NATAL-1'")
    _expect_frozen(conn, "DELETE FROM l0_rule_book_cards WHERE card_id='FIX-NATAL-1'")
    _expect_frozen(conn, "INSERT INTO l0_rule_book_cards SELECT rulebook_version, 'FIX-NEW', card_json || '{\"card_id\":\"FIX-NEW\"}', "
                         "card_sha256, ratification_sha256, redaction_map_json, NULL, NULL, category, polarity, provenance, verdict, "
                         "passage_ids, 'withdrawn', 'x', build_id, now() FROM l0_rule_book_cards WHERE card_id='FIX-NATAL-1'")
    _expect_frozen(conn, "DELETE FROM l0_rule_book_card_classes WHERE card_id='FIX-NATAL-1'")
    _expect_frozen(conn, "INSERT INTO l0_rule_book_card_classes VALUES ('FIXTURE-0.1','FIX-NATAL-1','major_loss')")
    _expect_frozen(conn, "UPDATE l0_rule_book_versions SET card_count = 7")
    _expect_frozen(conn, "UPDATE l0_rule_book_versions SET frozen_at = NULL")
    _expect_frozen(conn, "UPDATE l0_rule_book_versions SET change_register_ids = '{X}'")
    _expect_frozen(conn, "DELETE FROM l0_rule_book_versions")
    for t in ("l0_rule_book_cards", "l0_rule_book_card_classes", "l0_rule_book_versions"):
        _expect_frozen(conn, f"TRUNCATE {t} CASCADE")
    # the writer's own upsert SQL, aimed straight at the frozen version, is refused by the trigger too
    src = RB.load_source(RB.FIXTURE_MANIFEST, allow_fixture=True)
    with pytest.raises(psycopg.errors.ObjectNotInPrerequisiteState):
        with conn.cursor() as cur:
            cur.execute(RB._UPSERT_CARD, {
                "v": "FIXTURE-0.1", "card_id": "FIX-NATAL-1", "card_json": RB.Jsonb(src.rows[1].card),
                "card_sha256": src.rows[1].card_sha256, "rat": src.rows[1].ratification_sha256, "rmap": RB.Jsonb([]),
                "ir_json": RB.Jsonb(src.rows[1].result.ir), "ir_sha256": src.rows[1].result.ir_sha256,
                "category": "natal_promise", "polarity": "promotive", "provenance": "verse_cited", "verdict": "scored",
                "passage_ids": src.rows[1].passage_ids, "status": "active", "reason": None, "b": "x"})
    conn.rollback()
    assert conn.execute("SELECT COUNT(*) FROM l0_rule_book_cards").fetchone()[0] == 6


def test_freeze_time_checks_and_insert_unfrozen_only(clean):
    conn = clean
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    # card_count disagreeing with the rows refuses the freeze
    conn.execute("UPDATE l0_rule_book_versions SET card_count = 5")
    _expect_frozen(conn, "UPDATE l0_rule_book_versions SET card_count = 5, frozen_at = now()")
    # a card without a class row refuses the freeze
    conn.execute("DELETE FROM l0_rule_book_card_classes WHERE card_id = 'FIX-NATAL-1'")
    _expect_frozen(conn, "UPDATE l0_rule_book_versions SET frozen_at = now()")
    # a version cannot be born frozen
    _expect_frozen(conn, "INSERT INTO l0_rule_book_versions (rulebook_version, manifest_sha256, card_file_sha256, card_count, frozen_at) "
                         "VALUES ('TEST-BORN', repeat('a',64), repeat('b',64), 0, now())")


# ── one current version + count_sql ──────────────────────────────────────────
def test_one_current_version_and_count_sql(clean, tmp_path):
    conn = clean
    assert _count_sql(conn) == 0
    a = write_version(tmp_path / "a", "TEST-A", _pd_cards())                                  # 2 active
    restricted = K.natal_card()  # synthtext is not on the allowlist: stored redacted, quarantined
    restricted["card_id"] = "SYN-NATAL-R"
    b = write_version(tmp_path / "b", "TEST-B", _pd_cards() + [restricted],
                      withdrawn={"SYN-DASHA-1": "test withdrawal"})                          # 1 active, 1 withdrawn, 1 redacted->quarantined
    _run(conn, a)
    _run(conn, b)
    _run(conn, RB.FIXTURE_MANIFEST, rule_book_allow_fixture=True)
    # only a frozen version may be current
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("UPDATE l0_rule_book_versions SET is_current = true WHERE rulebook_version = 'TEST-A'")
    conn.rollback()
    for v in ("TEST-A", "TEST-B", "FIXTURE-0.1"):
        _freeze(conn, v)
    # a FIXTURE version can never be current
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("UPDATE l0_rule_book_versions SET is_current = true WHERE rulebook_version = 'FIXTURE-0.1'")
    conn.rollback()
    with pytest.raises(psycopg.errors.CheckViolation):  # case-insensitive
        conn.execute("INSERT INTO l0_rule_book_versions (rulebook_version, manifest_sha256, card_file_sha256, card_count) "
                     "VALUES ('fixture-lower', repeat('a',64), repeat('b',64), 0); "
                     "UPDATE l0_rule_book_versions SET frozen_at = now() WHERE rulebook_version = 'fixture-lower'; "
                     "UPDATE l0_rule_book_versions SET is_current = true WHERE rulebook_version = 'fixture-lower'")
    conn.rollback()
    assert _count_sql(conn) == 0  # nothing current yet
    conn.execute("UPDATE l0_rule_book_versions SET is_current = true WHERE rulebook_version = 'TEST-A'")
    conn.commit()
    with pytest.raises(psycopg.errors.UniqueViolation):
        conn.execute("UPDATE l0_rule_book_versions SET is_current = true WHERE rulebook_version = 'TEST-B'")
    conn.rollback()

    def expected(path):
        return sum(1 for r in RB.load_source(path).rows if r.status == "active")

    assert expected(a) == 2 and _count_sql(conn) == 2
    # moving the pointer is allowed on frozen versions (is_current is not content): two statements, one transaction
    conn.execute("UPDATE l0_rule_book_versions SET is_current = false WHERE rulebook_version = 'TEST-A'")
    conn.execute("UPDATE l0_rule_book_versions SET is_current = true WHERE rulebook_version = 'TEST-B'")
    conn.commit()
    assert expected(b) == 1 and _count_sql(conn) == 1
    statuses = dict(conn.execute(
        "SELECT card_id, status FROM l0_rule_book_cards WHERE rulebook_version='TEST-B'").fetchall())
    assert statuses == {"SYN-NATAL-1": "active", "SYN-DASHA-1": "withdrawn", "SYN-NATAL-R": "quarantined_not_evaluable"}
    assert conn.execute("SELECT COUNT(*) FROM l0_rule_book_versions WHERE is_current").fetchone()[0] == 1
