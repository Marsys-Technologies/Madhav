from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_vidhi_floors import FLOORS, VidhiFloorsWriter


class Cursor:
    def __init__(self, owner):
        self.owner = owner
        self.rowcount = 1

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return False

    def execute(self, sql, params=None):
        self.owner.statements.append((" ".join(sql.split()), params))

    def fetchone(self):
        return {"intent_count": len(FLOORS), "item_count": sum(len(f[-1]) for f in FLOORS)}


class Conn:
    def __init__(self):
        self.statements = []

    def cursor(self):
        return Cursor(self)


def test_rebuild_removes_obsolete_intents_and_fails_closed_on_exact_counts():
    conn = Conn()
    result = VidhiFloorsWriter().run(ContextSpec(
        asset_id="bg_vidhi_floors", build_id="build", db_conn=conn,
    ))

    statements = [sql for sql, _ in conn.statements]
    obsolete_delete = next(sql for sql in statements if sql.startswith("DELETE FROM vidhi_intent_floors"))
    assert "NOT (intent = ANY(%s))" in obsolete_delete
    assert any("AS intent_count" in sql and "AS item_count" in sql for sql in statements)
    assert result.rows_inserted == len(FLOORS) + sum(len(f[-1]) for f in FLOORS)
    assert "total_owned=423" in result.notes


def test_dry_run_reports_headers_and_items_as_owned_rows():
    result = VidhiFloorsWriter().run(ContextSpec(
        asset_id="bg_vidhi_floors", build_id="build", db_conn=object(), dry_run=True,
    ))

    assert result.rows_inserted == len(FLOORS) + sum(len(f[-1]) for f in FLOORS)
    assert "total_owned=423" in result.notes
