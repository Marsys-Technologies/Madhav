"""Suvarna Track I-4 / I-5: output-digest specs that let `ka_vighnakara` (I-4) and
the two writer-backed services `ka_dasha_kala` / `ka_muhurta_seva` (I-5, the
`ka_sangam` upstream-digest blocker) reach a 'proven' receipt.

Layer 1 (no DB): each migration's spec passes the REAL `_validate_spec`, carries no
volatile / surrogate column, and orders on every column it hashes.
Layer 2 (disposable Postgres, `I45_DIGEST_DSN`; NOT_RUN/skip when unreachable, never
any other DSN): the REAL `compute_output_digest` is run against the migration's
verbatim spec: digest is produced, stable across two identical rebuilds, and moves
when a hashed output value moves.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from pipeline.orchestrator.output_digest import (  # noqa: E402
    _validate_spec,
    compute_output_digest,
)

ROOT = Path(__file__).resolve().parents[3]
MIG_VIGHNAKARA = ROOT / "migrations/1212_nirmana_l3_ka_vighnakara_output_digest_spec.sql"
MIG_SERVICES = ROOT / "migrations/1213_nirmana_l3_service_selftest_output_digest_specs.sql"
CANONICAL = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER_CHART = "1c826d5a-0000-4000-8000-000000000001"

DSN = os.environ.get("I45_DIGEST_DSN")

_VALUE_RE = (
    r"VALUES\s*\(\s*'{asset}'\s*,\s*'([a-f0-9]{{64}})'\s*,\s*'(\{{.*?\}})'::jsonb\s*\)"
)


def _spec(path: Path, asset_id: str) -> tuple[str, dict]:
    sql = path.read_text()
    match = re.search(_VALUE_RE.format(asset=asset_id), sql, flags=re.DOTALL)
    assert match is not None, f"{asset_id} spec row not found in {path.name}"
    return match.group(1), json.loads(match.group(2))


# ── Layer 1: contract (no DB) ────────────────────────────────────────────────

VOLATILE_OR_SURROGATE = {"id", "computed_at", "convergence_id", "source_citation", "last_selftest_at"}


@pytest.mark.parametrize(
    "path,asset", [(MIG_VIGHNAKARA, "ka_vighnakara"), (MIG_SERVICES, "ka_dasha_kala"),
                   (MIG_SERVICES, "ka_muhurta_seva")],
)
def test_spec_passes_real_validator_and_migration_is_ddl_safe(path, asset) -> None:
    sql = path.read_text()
    sha, spec = _spec(path, asset)
    assert _validate_spec(asset, spec, sha).spec_sha256 == sha
    assert "\nBEGIN;" not in sql and "\nCOMMIT;" not in sql
    assert "ON CONFLICT (asset_id, spec_sha256) DO NOTHING" in sql
    assert not re.search(r"\b(DROP|TRUNCATE|DELETE|ALTER)\b\s", re.sub(r"--.*", "", sql), re.I)
    assert "SET LOCAL lock_timeout = '5s'" in sql


def test_vighnakara_spec_hashes_content_not_execution_history() -> None:
    _, spec = _spec(MIG_VIGHNAKARA, "ka_vighnakara")
    (component,) = spec["components"]
    assert component["relation"] == "kala_obstruction"
    assert component["where_equals"] == {"chart_id": CANONICAL}
    values, keys = component["value_columns"], component["key_columns"]
    assert not VOLATILE_OR_SURROGATE & set(values), "volatile/surrogate column hashed"
    assert not VOLATILE_OR_SURROGATE & set(keys)
    # Every hashed column except the where_equals-pinned constant must be an ordering
    # key: that makes the row order total over the hashed projection, so a tie can
    # only be between byte-identical rows and the digest cannot depend on heap order.
    assert set(values) - {"chart_id"} <= set(keys)
    # The columns that carry the obstruction's meaning are all hashed.
    assert {"signal_id", "obstruction_type", "severity", "severity_score",
            "override_score", "obstruction_detail"} <= set(values)


@pytest.mark.parametrize("asset", ["ka_dasha_kala", "ka_muhurta_seva"])
def test_service_spec_hashes_health_verdict_not_timestamp(asset) -> None:
    _, spec = _spec(MIG_SERVICES, asset)
    (component,) = spec["components"]
    assert component["relation"] == "asset_registry"
    assert component["where_equals"] == {"asset_id": asset}
    assert component["key_columns"] == ["asset_id"]
    assert component["value_columns"] == ["asset_id", "service_health", "selftest_detail"]
    assert not VOLATILE_OR_SURROGATE & set(component["value_columns"])


# ── Layer 1b: spec columns exist in the governed DDL (no DB) ─────────────────

_MIG_TREES = (ROOT / "migrations", ROOT / "supabase/migrations")


def _all_sql() -> dict[Path, str]:
    return {p: re.sub(r"--[^\n]*", "", p.read_text()) for t in _MIG_TREES for p in sorted(t.glob("*.sql"))}


def _create_table_columns(sql: str, table: str) -> set[str]:
    """Column names of the LAST `CREATE TABLE <table> (...)` in `sql`."""
    starts = [m.end() for m in re.finditer(
        r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?%s\s*\(" % table, sql, re.I)]
    assert starts, f"no CREATE TABLE {table}"
    depth, i, parts, cur = 1, starts[-1], [], ""
    while depth:
        ch = sql[i]
        depth += ch == "("
        depth -= ch == ")"
        if depth == 1 and ch == ",":
            parts.append(cur)
            cur = ""
        elif depth:
            cur += ch
        i += 1
    parts.append(cur)
    skip = {"constraint", "primary", "unique", "foreign", "check", "like", "exclude"}
    cols = set()
    for part in parts:
        tok = part.split()[:1]
        if tok and tok[0].strip('"').lower() not in skip:
            cols.add(tok[0].strip('"').lower())
    return cols


def _altered_columns(table: str) -> tuple[set[str], list[str]]:
    """(columns added by ALTER TABLE ... ADD COLUMN, DROP/RENAME COLUMN statements) in either tree."""
    added, removed = set(), []
    for path, sql in _all_sql().items():
        for stmt in re.findall(r"ALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:ONLY\s+)?(?:public\.)?%s\b[^;]*;" % table, sql, re.I):
            added |= {c.lower() for c in re.findall(r"ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?\"?(\w+)", stmt, re.I)}
            if re.search(r"(DROP|RENAME)\s+COLUMN", stmt, re.I):
                removed.append(f"{path.name}: {stmt[:80]}")
    return added, removed


def _spec_columns(path: Path, asset: str) -> set[str]:
    _, spec = _spec(path, asset)
    cols: set[str] = set()
    for comp in spec["components"]:
        cols |= set(comp["key_columns"]) | set(comp["value_columns"])
        cols |= set(comp.get("where_equals") or {}) | set(comp.get("where_in") or {})
        cols |= set(comp.get("where_is_null") or [])
    return cols


def test_vighnakara_spec_columns_exist_in_kala_obstruction_ddl() -> None:
    ddl = _all_sql()[ROOT / "supabase/migrations/245_l3_ka_vighnakara.sql"]
    cols = _create_table_columns(ddl, "kala_obstruction")
    added, removed = _altered_columns("kala_obstruction")
    assert not removed, f"later migration drops/renames kala_obstruction columns: {removed}"
    # 245 DROPs and re-CREATEs the table; nothing after it may re-create it differently.
    later_creates = [p.name for p, sql in _all_sql().items()
                     if re.search(r"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?(public\.)?kala_obstruction\b", sql, re.I)
                     and p.name not in ("245_l3_ka_vighnakara.sql", "brahma_kala_obstruction.sql",
                                        "0001_brahma_baseline.sql", "0000_seed_legacy_applied.sql",
                                        "0000b_seed_legacy_v2.sql", "_pre_squash_schema_snapshot.psql")]
    assert not later_creates, later_creates
    missing = _spec_columns(MIG_VIGHNAKARA, "ka_vighnakara") - (cols | added)
    assert not missing, f"spec names columns absent from kala_obstruction DDL: {sorted(missing)}"


@pytest.mark.parametrize("asset", ["ka_dasha_kala", "ka_muhurta_seva"])
def test_service_spec_columns_exist_in_asset_registry_ddl(asset) -> None:
    base = _create_table_columns(_all_sql()[ROOT / "supabase/migrations/167_asset_registry.sql"], "asset_registry")
    added, removed = _altered_columns("asset_registry")
    assert not removed, f"later migration drops/renames asset_registry columns: {removed}"
    missing = _spec_columns(MIG_SERVICES, asset) - (base | added)
    assert not missing, f"spec names columns absent from asset_registry DDL: {sorted(missing)}"


def test_ddl_column_parser_finds_the_known_columns() -> None:
    """Guard the parser itself: it must see real columns, else the checks above are vacuous."""
    ddl = _all_sql()[ROOT / "supabase/migrations/245_l3_ka_vighnakara.sql"]
    assert {"id", "chart_id", "signal_id", "obstruction_detail", "computed_at"} <= \
        _create_table_columns(ddl, "kala_obstruction")
    added, _ = _altered_columns("asset_registry")
    assert {"service_health", "selftest_detail", "last_selftest_at"} <= added


@pytest.mark.parametrize("path,asset", [(MIG_VIGHNAKARA, "ka_vighnakara"), (MIG_SERVICES, "ka_dasha_kala"),
                                        (MIG_SERVICES, "ka_muhurta_seva")])
def test_literal_sha_equals_canonical_digest_of_spec(path, asset) -> None:
    from pipeline.orchestrator.provenance import canonical_digest
    sha, spec = _spec(path, asset)
    assert canonical_digest(spec) == sha


# ── Layer 2: real compute_output_digest on a disposable Postgres ─────────────

DDL = """
DROP TABLE IF EXISTS kala_obstruction, asset_registry, asset_output_digest_specs CASCADE;
CREATE TABLE asset_output_digest_specs (
    asset_id TEXT NOT NULL, spec_sha256 TEXT NOT NULL, spec JSONB NOT NULL,
    retired_at TIMESTAMPTZ, PRIMARY KEY (asset_id, spec_sha256));
-- migration 245 shape (FKs omitted: the referenced tables are not under test)
CREATE TABLE kala_obstruction (
    id BIGSERIAL PRIMARY KEY,
    chart_id UUID NOT NULL,
    convergence_id BIGINT,
    signal_id UUID,
    obstruction_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    severity_score DOUBLE PRECISION NOT NULL,
    override_score DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    obstruction_detail JSONB NOT NULL DEFAULT '{}',
    source_citation TEXT NOT NULL DEFAULT 'ka_vighnakara:v1.0',
    computed_at TIMESTAMPTZ DEFAULT NOW());
CREATE TABLE asset_registry (
    asset_id TEXT PRIMARY KEY, service_health TEXT, last_selftest_at TIMESTAMPTZ,
    selftest_detail JSONB);
"""

S1, S2, S3 = ("00000000-0000-4000-8000-00000000000%d" % i for i in (1, 2, 3))


@pytest.fixture()
def db():
    if not DSN:
        pytest.skip("NOT_RUN: set I45_DIGEST_DSN to a disposable Postgres")
    import psycopg
    from psycopg.rows import dict_row
    try:
        conn = psycopg.connect(DSN, connect_timeout=5, row_factory=dict_row)
    except Exception:
        pytest.skip("NOT_RUN: disposable Postgres unreachable")
    conn.execute(DDL)
    for path in (MIG_VIGHNAKARA, MIG_SERVICES):
        conn.execute(path.read_text())          # verbatim, as the deploy runner would
    conn.execute("INSERT INTO asset_registry (asset_id) VALUES "
                 "('ka_dasha_kala'), ('ka_muhurta_seva'), ('ka_sangam')")
    yield conn
    conn.rollback()
    conn.close()


def _obs(conn, rows, chart=CANONICAL, *, conv_base=100):
    """Insert rows [(signal, type, sev, score, override, detail)] as the writer does."""
    for i, (sig, typ, sev, score, ovr, detail) in enumerate(rows):
        conn.execute(
            "INSERT INTO kala_obstruction (chart_id, convergence_id, signal_id, obstruction_type,"
            " severity, severity_score, override_score, obstruction_detail, source_citation)"
            " VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s)",
            (chart, conv_base + i if detail.get("anchor") != "dasha_timeline" else None, sig, typ,
             sev, score, ovr, json.dumps(detail), f"ka_vighnakara:v2.0:conv={conv_base + i}"),
        )


def _digest(conn, asset="ka_vighnakara"):
    return compute_output_digest(conn.cursor(), asset_id=asset)


ROWS = [
    (S1, "malefic_transit", "moderate", 0.6, 0.27, {"planet": "Saturn", "peak_date": "2026-03-01"}),
    (S1, "gandanta", "mild", 0.3, 0.135, {"peak_date": "2026-03-01"}),
    (S2, "malefic_transit", "moderate", 0.6, 0.27, {"planet": "Saturn", "peak_date": "2026-03-01"}),
    (S3, "papakartari", "severe", 0.9, 0.4, {"peak_date": "2027-01-01", "anchor": "dasha_timeline"}),
]


def test_vighnakara_digest_and_spec_sha_are_produced(db) -> None:
    _obs(db, ROWS)
    digest, spec_sha = _digest(db)
    assert re.fullmatch(r"[a-f0-9]{64}", digest)
    assert spec_sha == _spec(MIG_VIGHNAKARA, "ka_vighnakara")[0]


def test_vighnakara_digest_stable_across_identical_rebuild(db) -> None:
    """Rebuild = delete-then-insert: new ids, new convergence ids, new computed_at,
    new source_citation, and a different physical row order. Digest must not move."""
    _obs(db, ROWS, conv_base=100)
    first, _ = _digest(db)
    db.execute("DELETE FROM kala_obstruction WHERE chart_id = %s", (CANONICAL,))
    _obs(db, list(reversed(ROWS)), conv_base=9000)
    second, _ = _digest(db)
    assert first == second


def test_vighnakara_tie_between_rows_differing_only_in_signal_is_order_independent(db) -> None:
    """ROWS[0] and ROWS[2] differ only in signal_id. Swapping their insertion order
    must not move the digest (the ordering has to reach signal_id)."""
    _obs(db, [ROWS[0], ROWS[2]])
    a, _ = _digest(db)
    db.execute("DELETE FROM kala_obstruction")
    _obs(db, [ROWS[2], ROWS[0]])
    b, _ = _digest(db)
    assert a == b


@pytest.mark.parametrize("mutate_sql", [
    "UPDATE kala_obstruction SET severity_score = 0.61 WHERE obstruction_type = 'gandanta'",
    "UPDATE kala_obstruction SET override_score = 0.5 WHERE obstruction_type = 'gandanta'",
    "UPDATE kala_obstruction SET severity = 'severe' WHERE obstruction_type = 'gandanta'",
    "UPDATE kala_obstruction SET obstruction_type = 'combustion' WHERE obstruction_type = 'gandanta'",
    "UPDATE kala_obstruction SET obstruction_detail = '{\"peak_date\": \"2026-03-02\"}'::jsonb "
    "WHERE obstruction_type = 'gandanta'",
    "UPDATE kala_obstruction SET signal_id = '00000000-0000-4000-8000-0000000000ff' "
    "WHERE obstruction_type = 'gandanta'",
    "DELETE FROM kala_obstruction WHERE obstruction_type = 'gandanta'",
    "INSERT INTO kala_obstruction (chart_id, signal_id, obstruction_type, severity, severity_score)"
    " VALUES ('%s', '00000000-0000-4000-8000-00000000000a', 'combustion', 'mild', 0.2)" % CANONICAL,
], ids=["severity_score", "override_score", "severity", "type", "detail", "signal", "row_removed",
        "row_added"])
def test_vighnakara_digest_changes_when_an_output_value_changes(db, mutate_sql) -> None:
    _obs(db, ROWS)
    before, _ = _digest(db)
    db.execute(mutate_sql)
    after, _ = _digest(db)
    assert before != after


def test_vighnakara_digest_ignores_other_charts_and_surrogates(db) -> None:
    _obs(db, ROWS)
    before, _ = _digest(db)
    _obs(db, ROWS[:2], chart=OTHER_CHART, conv_base=500)           # another chart's rows
    db.execute("UPDATE kala_obstruction SET computed_at = NOW() + interval '1 day',"
               " source_citation = 'x', convergence_id = id + 7777 WHERE chart_id = %s", (CANONICAL,))
    assert _digest(db)[0] == before


def test_vighnakara_null_signal_row_fails_closed_not_silently_hashed(db) -> None:
    _obs(db, ROWS)
    db.execute("INSERT INTO kala_obstruction (chart_id, signal_id, obstruction_type, severity,"
               " severity_score) VALUES (%s, NULL, 'gandanta', 'mild', 0.1)", (CANONICAL,))
    with pytest.raises(ValueError, match="NULL reviewed key"):
        _digest(db)


@pytest.mark.parametrize("asset", ["ka_dasha_kala", "ka_muhurta_seva"])
def test_service_digest_produced_stable_and_moves_with_health_verdict(db, asset) -> None:
    detail = {"systems_found": ["mudda", "vimshottari"], "windows_returned": 12}
    db.execute("UPDATE asset_registry SET service_health='healthy', last_selftest_at=NOW(),"
               " selftest_detail=%s::jsonb WHERE asset_id=%s", (json.dumps(detail), asset))
    first, sha = _digest(db, asset)
    assert re.fullmatch(r"[a-f0-9]{64}", first)
    assert sha == _spec(MIG_SERVICES, asset)[0]
    # identical self-test, later timestamp (what a re-run does) -> same digest
    db.execute("UPDATE asset_registry SET last_selftest_at = NOW() + interval '1 hour' WHERE asset_id=%s", (asset,))
    assert _digest(db, asset)[0] == first
    # a changed self-test outcome moves it
    db.execute("UPDATE asset_registry SET selftest_detail = %s::jsonb WHERE asset_id=%s",
               (json.dumps({**detail, "windows_returned": 11}), asset))
    assert _digest(db, asset)[0] != first
    # restore the payload so the verdict flip below is the ONLY difference from `first`
    db.execute("UPDATE asset_registry SET selftest_detail = %s::jsonb WHERE asset_id=%s",
               (json.dumps(detail), asset))
    assert _digest(db, asset)[0] == first
    db.execute("UPDATE asset_registry SET service_health='degraded' WHERE asset_id=%s", (asset,))
    assert _digest(db, asset)[0] != first


def test_service_digest_is_scoped_to_its_own_registry_row(db) -> None:
    db.execute("UPDATE asset_registry SET service_health='healthy', selftest_detail='{\"a\":1}'::jsonb"
               " WHERE asset_id IN ('ka_dasha_kala','ka_muhurta_seva')")
    dk, _ = _digest(db, "ka_dasha_kala")
    db.execute("UPDATE asset_registry SET service_health='unhealthy' WHERE asset_id='ka_muhurta_seva'")
    db.execute("UPDATE asset_registry SET service_health='x' WHERE asset_id='ka_sangam'")
    assert _digest(db, "ka_dasha_kala")[0] == dk
    assert _digest(db, "ka_muhurta_seva")[0] != dk


def test_service_receipt_would_be_proven_and_upstream_hash_accepts_it(db) -> None:
    """End-to-end on the receipt predicate: with a digest AND a spec sha the receipt of
    a writer-backed service has no unknown reason, and `compute_upstream_hash`
    (asset_runner.py:236-247) takes a proven dep without any service accommodation."""
    from pipeline.orchestrator.provenance import build_receipt
    db.execute("UPDATE asset_registry SET service_health='healthy', selftest_detail='{\"a\":1}'::jsonb"
               " WHERE asset_id='ka_dasha_kala'")
    digest, sha = _digest(db, "ka_dasha_kala")
    receipt = build_receipt(
        asset_id="ka_dasha_kala", chart_id=None, code_digest="c" * 64, config={"chart_id": None},
        upstream_digest="u" * 64, upstream_receipts=[], partition_declaration=None,
        has_cowriters=False, output_digest=digest, output_digest_spec_sha256=sha)
    assert receipt.receipt_state == "proven" and receipt.unknown_reasons == ()
    # negative: the pre-fix shape (no spec -> (None, None)) is 'unknown' with both reasons
    bare = build_receipt(
        asset_id="ka_dasha_kala", chart_id=None, code_digest="c" * 64, config={"chart_id": None},
        upstream_digest="u" * 64, upstream_receipts=[], partition_declaration=None,
        has_cowriters=False, output_digest=None, output_digest_spec_sha256=None)
    assert bare.receipt_state == "unknown"
    assert {"output_digest_unavailable", "output_digest_spec_unavailable"} <= set(bare.unknown_reasons)


def test_upstream_hash_for_ka_sangam_needs_every_service_dep_digest(monkeypatch) -> None:
    """compute_upstream_hash (the NULL that blocks ka_sangam) is non-NULL once each
    service dep's latest receipt carries an output_digest, NULL while any lacks one."""
    from pipeline.orchestrator import asset_runner

    def receipts(muhurta_digest, dasha_digest):
        return [
            {"asset_id": "ka_dasha_kala", "output_digest": dasha_digest, "receipt_state": "proven",
             "asset_kind": "service", "service_health": "healthy"},
            {"asset_id": "ka_muhurta_seva", "output_digest": muhurta_digest, "receipt_state": "proven",
             "asset_kind": "service", "service_health": "healthy"},
        ]

    deps = ["ka_dasha_kala", "ka_muhurta_seva"]
    monkeypatch.setattr(asset_runner, "load_upstream_receipts", lambda *_: receipts("m" * 64, "d" * 64))
    ok = asset_runner.compute_upstream_hash(None, "ka_sangam", None, deps)
    assert ok is not None
    monkeypatch.setattr(asset_runner, "load_upstream_receipts", lambda *_: receipts("m" * 64, "e" * 64))
    assert asset_runner.compute_upstream_hash(None, "ka_sangam", None, deps) != ok   # moves with it
    monkeypatch.setattr(asset_runner, "load_upstream_receipts", lambda *_: receipts(None, "d" * 64))
    assert asset_runner.compute_upstream_hash(None, "ka_sangam", None, deps) is None  # pre-fix shape
