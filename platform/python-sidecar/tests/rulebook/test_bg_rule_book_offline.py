"""bg_rule_book (Rule Book engine E2) — offline tests: source verification, licence refusal,
redaction, fixture guard, registration and migration/registry consistency. No database.

The DB-backed tests (migration, trigger, idempotency, count_sql) are in test_bg_rule_book_db.py.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from brahmagyan import l0_rule_book as RB
from services.rulebook import constants as RC
from services.rulebook.compiler import sha256_hex
from services.rulebook.lints import lint_licence
from tests.rulebook import _cards as K
from tests.rulebook._rule_book_versions import fixture_cards, write_version

SIDECAR = Path(__file__).resolve().parents[2]
REPO = SIDECAR.parents[1]
MIGRATION = REPO / "platform" / "migrations" / "1413_bg_rule_book_l0_store.sql"
SEED = REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"


class _RecordingConn:
    """Stands in for ctx.db_conn where no write may happen; records every call."""

    def __init__(self):
        self.calls = []

    def cursor(self):
        conn = self

        class _Cur:
            rowcount = 0

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def execute(self, sql, params=None):
                conn.calls.append(("execute", " ".join(sql.split())[:60]))

            def fetchone(self):
                return None

        return _Cur()

    def commit(self):
        self.calls.append(("commit",))

    def rollback(self):
        self.calls.append(("rollback",))

    def close(self):
        self.calls.append(("close",))


def _pd(card: dict) -> dict:
    """Move a synthetic _cards.py card onto the public-domain text id (invented prose)."""
    cite = card["field1_citation"]
    cite["text_id"] = "sarvartha_chintamani"
    cite["passage_ids"] = ["sarvartha_chintamani_pg9001_c01:en:p001"]
    cite["chunk_id"] = "sarvartha_chintamani_pg9001_c01"
    for k in ("frame_citation",):
        fc = (card.get("field3_reference_frame") or {}).get(k)
        if fc:
            fc["passage_ids"] = ["sarvartha_chintamani_pg9001_c01:en:p000"]
    return card


# ── the committed FIXTURE ────────────────────────────────────────────────────
def test_fixture_loads_with_expected_statuses():
    src = RB.load_source(RB.FIXTURE_MANIFEST, allow_fixture=True)
    got = {r.card_id: r.status for r in src.rows}
    assert got == {
        "FIX-DASHA-1": "active",
        "FIX-NATAL-1": "active",
        "FIX-QUAR-MEAN-1": "quarantined_not_evaluable",
        "FIX-REDACTED-1": "quarantined_not_evaluable",
        "FIX-TESTIMONY-1": "active",
        "FIX-WITHDRAWN-1": "withdrawn",
    }
    rows = {r.card_id: r for r in src.rows}
    assert rows["FIX-TESTIMONY-1"].verdict == "testimony"
    assert rows["FIX-NATAL-1"].verdict == "scored"
    assert rows["FIX-DASHA-1"].class_groups == ["career_setback", "major_loss"]
    assert "MEAN_OPERAND" in rows["FIX-QUAR-MEAN-1"].quarantine_reason
    assert rows["FIX-WITHDRAWN-1"].quarantine_reason.startswith("withdrawn: ")
    for r in src.rows:
        assert (r.status == "active") == (r.quarantine_reason is None)
        if r.status == "active":
            assert r.result.ir is not None and r.result.ir["status"] == "active"


def test_fixture_has_no_restricted_quote_text():
    for card in fixture_cards():
        assert lint_licence(card) == [], card["card_id"]
    red = {r.card_id: r for r in RB.load_source(RB.FIXTURE_MANIFEST, allow_fixture=True).rows}["FIX-REDACTED-1"]
    assert "quote" not in red.card["field1_citation"]
    assert red.redaction_map and red.ratification_sha256 != red.card_sha256


def test_fixture_refused_without_opt_in():
    with pytest.raises(RB.RuleBookSourceError, match="FIXTURE"):
        RB.load_source(RB.FIXTURE_MANIFEST)


def test_production_default_manifest_absent_raises():
    assert not RB.DEFAULT_MANIFEST.exists()
    with pytest.raises(RB.RuleBookSourceError, match="no rule-book manifest"):
        RB.seed_rule_book(_RecordingConn())


def test_fixture_flag_and_prefix_must_agree(tmp_path):
    for v in ("FIXTURE-X", "fixture-x"):  # prefix without the flag, either case
        path = write_version(tmp_path / v, v, fixture_cards()[:1], redact=False)
        with pytest.raises(RB.RuleBookSourceError, match="fixture=true"):
            RB.load_source(path, allow_fixture=True)


# ── licence refusal (M5, Q7) ─────────────────────────────────────────────────
def test_licence_refuses_restricted_quote_and_writes_nothing(tmp_path):
    cards = fixture_cards()
    bad = cards[0]
    bad["field1_citation"]["text_id"] = "phaladeepika"
    bad["field1_citation"]["passage_ids"] = ["phaladeepika_pg9001_c01:en:p001"]
    path = write_version(tmp_path, "TEST-LIC", cards, redact=False)
    conn = _RecordingConn()
    with pytest.raises(RB.RuleBookLicenceRefused, match="QUOTE_RESTRICTED_EDITION"):
        RB.seed_rule_book(conn, manifest_path=path)
    assert conn.calls == []


def test_licence_refuses_nested_restricted_quote(tmp_path):
    cards = fixture_cards()
    cards[1]["field3_reference_frame"]["frame_citation"] = {
        "passage_ids": ["bphs_pg9001_c01:en:p000"],
        "quote": "invented frame words for a test only",
    }
    path = write_version(tmp_path, "TEST-LIC2", cards, redact=False)
    with pytest.raises(RB.RuleBookLicenceRefused):
        RB.load_source(path)


# ── redaction ────────────────────────────────────────────────────────────────
def test_redaction_hashes_and_restore():
    full = K.natal_card()  # synthtext: not on the allowlist, so restricted
    red, rmap, rat = RB.redact_card(full)
    assert rat == sha256_hex(full)
    assert lint_licence(red) == []
    assert [e["path"] for e in rmap] == ["/field1_citation"]
    quote = full["field1_citation"]["quote"]
    assert rmap[0]["quote_sha256"] == hashlib.sha256(quote.encode("utf-8")).hexdigest()
    bank = {rmap[0]["quote_sha256"]: quote}
    assert sha256_hex(RB.restore_card(red, rmap, bank)) == rat
    with pytest.raises(RB.RuleBookSourceError):
        RB.restore_card(red, rmap, {rmap[0]["quote_sha256"]: quote + " "})


def test_public_domain_quote_is_not_redacted():
    full = _pd(K.natal_card())
    red, rmap, rat = RB.redact_card(full)
    assert rmap == [] and red == full and rat == sha256_hex(red)


def test_redaction_path_still_carrying_text_is_refused(tmp_path):
    path = write_version(tmp_path, "TEST-RMAP", [K.natal_card()])
    m = json.loads(path.read_text())
    cards_path = path.parent / m["card_file"]
    doc = json.loads(cards_path.read_text())
    doc["cards"][0]["field1_citation"]["quote"] = ""  # blank, then claim it was redacted elsewhere
    m["cards"][0]["redaction_map"][0]["path"] = "/field3_reference_frame"
    doc["cards"][0]["field3_reference_frame"]["quote"] = "left behind"
    raw = (json.dumps(doc, sort_keys=True) + "\n").encode()
    cards_path.write_bytes(raw)
    m["card_file_sha256"] = hashlib.sha256(raw).hexdigest()
    m["cards"][0]["card_sha256"] = sha256_hex(doc["cards"][0])
    path.write_text(json.dumps(m))
    with pytest.raises(RB.RuleBookError):
        RB.load_source(path)


def test_empty_redaction_map_requires_equal_hashes(tmp_path):
    path = write_version(tmp_path, "TEST-RAT", [_pd(K.natal_card())])
    m = json.loads(path.read_text())
    m["cards"][0]["ratification_sha256"] = "0" * 64
    path.write_text(json.dumps(m))
    with pytest.raises(RB.RuleBookSourceError, match="must equal card_sha256"):
        RB.load_source(path)


# ── source tamper detection ──────────────────────────────────────────────────
def test_card_file_bytes_tamper_refused(tmp_path):
    path = write_version(tmp_path, "TEST-TAMPER", [_pd(K.natal_card())])
    cards_path = path.parent / json.loads(path.read_text())["card_file"]
    cards_path.write_bytes(cards_path.read_bytes() + b" ")
    with pytest.raises(RB.RuleBookSourceError, match="card file sha256"):
        RB.load_source(path)


def test_card_sha_tamper_refused(tmp_path):
    path = write_version(tmp_path, "TEST-CSHA", [_pd(K.natal_card())])
    m = json.loads(path.read_text())
    m["cards"][0]["card_sha256"] = "f" * 64
    path.write_text(json.dumps(m))
    with pytest.raises(RB.RuleBookSourceError, match="card_sha256"):
        RB.load_source(path)


def test_manifest_and_card_file_must_list_the_same_cards(tmp_path):
    path = write_version(tmp_path, "TEST-SET", [_pd(K.natal_card()), _pd(K.dasha_card())])
    m = json.loads(path.read_text())
    m["cards"] = m["cards"][:1]
    path.write_text(json.dumps(m))
    with pytest.raises(RB.RuleBookSourceError, match="same set"):
        RB.load_source(path)


def test_declared_status_other_than_withdrawn_refused(tmp_path):
    path = write_version(tmp_path, "TEST-STAT", [_pd(K.natal_card())])
    m = json.loads(path.read_text())
    m["cards"][0]["status"] = "quarantined_not_evaluable"
    path.write_text(json.dumps(m))
    with pytest.raises(RB.RuleBookSourceError, match="only withdrawn"):
        RB.load_source(path)


# ── build_fail lint refuses the version (P4) ─────────────────────────────────
def test_p4_double_transit_refuses_the_version(tmp_path):
    j = {"id": "ju", "role": "transiting_graha", "doctrinal_graha": "guru", "relation": "transits", "bhava": 7,
         "quote_terms": ["great planet", "seventh"]}
    s = {"id": "sa", "role": "transiting_graha", "doctrinal_graha": "shani", "relation": "transits", "bhava": 7,
         "quote_terms": ["slow planet", "seventh"]}
    path = write_version(tmp_path, "TEST-P4", [_pd(K.two_transit_card(j, s))])
    with pytest.raises(RB.RuleBookBuildLintRefused, match="P4_DOUBLE_TRANSIT"):
        RB.load_source(path)


# ── writer contract (no DB) ──────────────────────────────────────────────────
def test_writer_registered_and_never_commits_on_dry_run():
    from pipeline.orchestrator.writers import ContextSpec, get_writer
    from pipeline.orchestrator.writers.bg_rule_book import RuleBookWriter

    assert get_writer("bg_rule_book") is RuleBookWriter
    conn = _RecordingConn()
    ctx = ContextSpec(asset_id="bg_rule_book", build_id="t", db_conn=conn, dry_run=True,
                      config={"rule_book_manifest": str(RB.FIXTURE_MANIFEST), "rule_book_allow_fixture": True,
                              "chart_id": "00000000-0000-0000-0000-000000000000"})
    res = RuleBookWriter().run(ctx)
    assert res.rows_inserted == 6 and "[dry run]" in res.notes
    assert [c[0] for c in conn.calls] == ["execute"]  # the frozen-version probe only
    assert not any(c[0] in ("commit", "rollback", "close") for c in conn.calls)


def test_writer_module_never_touches_asset_throughput_or_chart_id():
    for f in (SIDECAR / "pipeline/orchestrator/writers/bg_rule_book.py", SIDECAR / "brahmagyan/l0_rule_book.py"):
        code = "\n".join(l for l in f.read_text().splitlines() if not l.lstrip().startswith(("#", "*", "``")))
        assert "asset_throughput" not in re.sub(r'"""[\s\S]*?"""', "", code)
        assert ".commit(" not in code and ".rollback(" not in code and ".close(" not in code
        assert "config['chart_id']" not in code and 'config.get("chart_id")' not in code


# ── migration ↔ constants ↔ seed consistency ─────────────────────────────────
def _strip_comments(sql: str) -> str:
    return "\n".join(l.split("--", 1)[0] for l in sql.splitlines())


def test_migration_has_no_transaction_control_and_matches_class_groups():
    sql = _strip_comments(MIGRATION.read_text(encoding="utf-8"))
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", sql, re.IGNORECASE | re.MULTILINE)
    block = re.search(r"l0rbcc_class_group_ck CHECK \(class_group IN \(([^)]*)\)\)", sql).group(1)
    assert tuple(re.findall(r"'([a-z_]+)'", block)) == tuple(RC.CLASS_GROUPS)
    assert len(RC.CLASS_GROUPS) == 20


def test_count_sql_identical_in_migration_and_seed():
    sql = MIGRATION.read_text(encoding="utf-8")
    mig = re.search(r"'(SELECT COUNT\(\*\) FROM l0_rule_book_cards[^\n]*?)',\n", sql).group(1).replace("''", "'")
    seed = SEED.read_text(encoding="utf-8")
    block = seed[seed.index("asset_id: 'bg_rule_book'"):]
    seed_sql = re.search(r'count_sql:\s*"([^"]+)"', block).group(1)
    assert mig == seed_sql
    assert "v.is_current" in mig and "v.frozen_at IS NOT NULL" in mig and "c.status = 'active'" in mig
