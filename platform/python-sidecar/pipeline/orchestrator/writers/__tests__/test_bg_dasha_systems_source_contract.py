"""Regression coverage for the complete governed dasha source."""

from brahmagyan.l0_dasha_systems import DASHA_SYSTEMS, seed_dasha_systems


def test_kp_is_writer_owned_and_source_identities_are_unique() -> None:
    identities = [system["canonical_id"] for system in DASHA_SYSTEMS]

    assert len(identities) == 20
    assert len(set(identities)) == 20
    assert "kp" in identities
    assert "chara_jaimini" in identities
    assert "jaimini_chara" not in identities


def test_writer_checks_all_three_projection_counts_after_replacement() -> None:
    class Cursor:
        rowcount = 1

        def __init__(self, owner):
            self.owner = owner

        def __enter__(self): return self
        def __exit__(self, *_exc): return False
        def execute(self, sql, params=None): self.owner.sql.append(" ".join(sql.split()))
        def fetchone(self):
            return {"catalog_count": 20, "ontology_count": 20, "reference_count": 20}

    class Conn:
        def __init__(self): self.sql = []
        def cursor(self): return Cursor(self)

    conn = Conn()
    seed_dasha_systems(conn, autocommit=False)
    assert any("AS catalog_count" in sql and "AS reference_count" in sql for sql in conn.sql)
