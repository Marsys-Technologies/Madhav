"""K0A-R1: execute the governed seed and alias in CI's disposable database."""
from pathlib import Path
import uuid

import psycopg
from psycopg import sql
import pytest


MIGRATIONS = Path(__file__).resolve().parents[5] / "supabase/migrations"
ALIAS = MIGRATIONS / "1331_kala_field_weight_canonical_system_keys.sql"


@pytest.fixture
def weights(kala_db_dsn):
    # 491 contains its own BEGIN/COMMIT. A private schema plus autocommit
    # executes it verbatim and lets cleanup run even after the mutant errors.
    schema = "k0a2_weights_" + uuid.uuid4().hex
    with psycopg.connect(kala_db_dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            conn.execute((MIGRATIONS / "491_kala_field_weights_seed.sql").read_text())
            yield conn
        finally:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_cara_alias_is_inserted_into_the_real_491_seeded_weights_table(weights):
    weights.execute(ALIAS.read_text())
    assert weights.execute(
        "SELECT weight_value, prior_value, n_eff, clipped FROM kala_field_weights "
        "WHERE version_id = 'v0_classical' AND weight_id = 'w_s:chara_karaka'"
    ).fetchone() == (0.60, 0.60, 0, False)


def test_cara_alias_restores_only_the_missing_governed_parent_version(weights):
    weights.execute("DELETE FROM kala_field_weights WHERE version_id = 'v0_classical'")
    weights.execute("DELETE FROM kala_field_weight_versions WHERE version_id = 'v0_classical'")
    weights.execute(ALIAS.read_text())
    assert weights.execute(
        "SELECT version_id, status, scope, x_schema_version, n_events_used "
        "FROM kala_field_weight_versions WHERE version_id = 'v0_classical'"
    ).fetchone() == ('v0_classical', 'active', 'global', 'x12_v0', 0)


def test_cara_alias_oracle_kills_a_wrong_target_table_mutation(weights):
    mutant = ALIAS.read_text().replace(
        "INSERT INTO kala_field_weights", "INSERT INTO kala_field_weight_versions", 1,
    )
    with pytest.raises(psycopg.errors.UndefinedColumn):
        weights.execute(mutant)
    assert weights.execute(
        "SELECT 1 FROM kala_field_weights "
        "WHERE version_id = 'v0_classical' AND weight_id = 'w_s:chara_karaka'"
    ).fetchone() is None
