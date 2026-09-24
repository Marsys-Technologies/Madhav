"""G-10 (remainder §8.5): migration 1086 ga_strength output-digest revision —
spec contract (real validator) + disposable-DB application.

Pure contract checks mirror tests/test_purna_wealth_ashtakavarga_digest_spec.py
(no DB). The disposable-DB check applies the migration verbatim against a
minimal asset_output_digest_specs reproduction and asserts retire/insert,
idempotency, and the fail-closed guard. NOT_RUN (skip) when the disposable DB
is unreachable — never a fallback to any other DSN.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import psycopg
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from pipeline.orchestrator.output_digest import _validate_spec  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
MIGRATION_1086 = (
    ROOT / "migrations/1086_nirmana_l0_gochara_g10_ga_strength_contributor_digest_spec.sql"
)

OLD_SHA = "3743484c996bf41a9b957224fd5c54cf04f1f1de27ef91116726b60b483bb07a"
NEW_SHA = "52a0d2537dc43fc04effe54fd65a165a223e918b14544f96a0892e1df3987a97"

DSN = os.environ.get(
    "GOCHARA_REMAINDER_DSN", "postgresql://wp6:disposable@localhost:55434/wp6"
)

DDL = """
DROP TABLE IF EXISTS asset_output_digest_specs;
CREATE TABLE asset_output_digest_specs (
    asset_id    TEXT NOT NULL,
    spec_sha256 TEXT NOT NULL,
    spec        JSONB NOT NULL,
    retired_at  TIMESTAMPTZ,
    PRIMARY KEY (asset_id, spec_sha256)
);
"""

OLD_SPEC = (
    '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"chart_facts",'
    '"relation":"chart_facts","where_in":{"fact_category":["ashtakavarga_bindu_per_varga",'
    '"ashtakavarga_pinda_sarva_per_varga","graha_shadbala_total"]},"key_columns":["fact_id"],'
    '"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},'
    '"value_columns":["fact_id","chart_id","ayanamsha_id","fact_category","fact_subject",'
    '"fact_key","fact_value_text","fact_value_num","fact_value_jsonb","unit","citation_ref",'
    '"citation_human","source_calculation","verification_pass_status","engine_version",'
    '"salience_formula_ver","tolerance_arcsec","near_sign_boundary_flag",'
    '"near_nakshatra_boundary_flag","vargottama_flag_at_point","formula_provenance_text",'
    '"cross_ayanamsha_divergence_arcsec","formula_id"]}]}'
)


def _new_spec() -> tuple[str, dict]:
    sql = MIGRATION_1086.read_text()
    match = re.search(
        r"VALUES\s*\(\s*'ga_strength'\s*,\s*'([a-f0-9]{64})'\s*,\s*'(\{.*?\})'::jsonb\s*\)",
        sql,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group(1), json.loads(match.group(2))


def test_migration_1086_has_no_inner_transaction_and_fails_closed() -> None:
    sql = MIGRATION_1086.read_text()
    assert "\nBEGIN;" not in sql
    assert "\nCOMMIT;" not in sql
    assert "DO $$" in sql
    assert "spec_sha256 NOT IN" in sql
    assert OLD_SHA in sql
    assert NEW_SHA in sql
    assert "RAISE EXCEPTION" in sql
    assert "ON CONFLICT (asset_id, spec_sha256) DO NOTHING" in sql


def test_migration_1086_new_spec_passes_real_validator_with_contributor_category() -> None:
    spec_sha, spec = _new_spec()
    validated = _validate_spec("ga_strength", spec, spec_sha)
    assert validated.spec_sha256 == NEW_SHA
    component = spec["components"][0]
    assert component["where_in"]["fact_category"] == [
        "ashtakavarga_bindu_contributor",
        "ashtakavarga_bindu_per_varga",
        "ashtakavarga_pinda_sarva_per_varga",
        "graha_shadbala_total",
    ]


@pytest.fixture()
def db():
    try:
        conn = psycopg.connect(DSN, connect_timeout=5, autocommit=True)
    except Exception:
        pytest.skip("NOT_RUN: disposable remainder DB unreachable")
    with conn.cursor() as cur:
        cur.execute(DDL)
    yield conn
    conn.close()


def _apply(conn) -> None:
    conn.execute(MIGRATION_1086.read_text())


def test_migration_1086_applies_retires_and_is_idempotent(db) -> None:
    db.execute(
        "INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) "
        "VALUES ('ga_strength', %s, %s::jsonb)",
        (OLD_SHA, OLD_SPEC),
    )
    _apply(db)

    rows = db.execute(
        "SELECT spec_sha256, retired_at IS NULL AS active "
        "FROM asset_output_digest_specs WHERE asset_id = 'ga_strength' ORDER BY spec_sha256"
    ).fetchall()
    state = {r[0]: r[1] for r in rows}
    assert state == {OLD_SHA: False, NEW_SHA: True}

    # Idempotent: second apply is a no-op and leaves exactly one active row.
    _apply(db)
    active = db.execute(
        "SELECT count(*) FROM asset_output_digest_specs "
        "WHERE asset_id = 'ga_strength' AND retired_at IS NULL"
    ).fetchone()[0]
    assert active == 1


def test_migration_1086_refuses_unrecognised_active_spec(db) -> None:
    db.execute(
        "INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec) "
        "VALUES ('ga_strength', %s, %s::jsonb)",
        ("f" * 64, OLD_SPEC),
    )
    with pytest.raises(Exception, match="unrecognised active"):
        _apply(db)
