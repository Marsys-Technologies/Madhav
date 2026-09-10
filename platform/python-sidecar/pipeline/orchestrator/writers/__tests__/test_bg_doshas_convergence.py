"""Regression coverage for the complete bg_doshas replacement contract."""

import inspect

from brahmagyan.l0_doshas import seed_doshas


def test_writer_replaces_all_owned_projections() -> None:
    source = inspect.getsource(seed_doshas)

    assert "DELETE FROM reference_doshas" in source
    assert "DELETE FROM brahma_dosha_catalog" in source
    assert "DELETE FROM brahma_ontology WHERE entity_class = 'dosha'" in source
    assert "ON CONFLICT" not in source


def test_writer_checks_all_three_projection_counts_after_replacement() -> None:
    class Cursor:
        rowcount = 1

        def __init__(self, owner):
            self.owner = owner
            self.sql = ""

        def __enter__(self): return self
        def __exit__(self, *_exc): return False
        def execute(self, sql, params=None):
            self.sql = " ".join(sql.split())
            self.owner.sql.append(self.sql)
        def fetchone(self):
            if "information_schema.tables" in self.sql:
                return {"count": 1}
            return {"catalog_count": 79, "ontology_count": 79, "reference_count": 79}

    class Conn:
        def __init__(self): self.sql = []
        def cursor(self): return Cursor(self)

    conn = Conn()
    seed_doshas(conn, autocommit=False)
    assert any("AS catalog_count" in sql and "AS reference_count" in sql for sql in conn.sql)
