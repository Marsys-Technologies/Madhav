from services.kala_core.ontology import CLASS_ROSTER, load_event_ontology
from services.kala_core.vocab import NullReason


class Cursor:
    description = [
        ("event_class_id",), ("name_en",), ("domain",), ("signature_model",),
        ("magnitude_floor",), ("temporal_shape",), ("milestone_template",),
        ("evidence_requirements",),
    ]

    def __init__(self, rows):
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def execute(self, sql, params):
        self.sql, self.params = sql, params

    def fetchall(self):
        return self.rows


class Connection:
    def __init__(self, rows):
        self.cursor_instance = Cursor(rows)

    def cursor(self):
        return self.cursor_instance


def _row(event_class_id):
    return (event_class_id, event_class_id.replace("_", " "), "general", {},
            "moderate", None, None, {})


def test_loader_returns_the_registrys_single_27_class_roster_in_registry_order():
    conn = Connection([_row(event_class_id) for event_class_id in reversed(CLASS_ROSTER)])

    loaded = load_event_ontology(conn)

    assert tuple(row.event_class_id for row in loaded) == CLASS_ROSTER
    assert len(loaded) == 27
    assert "FROM brahma_event_ontology" in conn.cursor_instance.sql


def test_loader_keeps_class_valence_honestly_null_with_its_declared_reason():
    loaded = load_event_ontology(Connection([_row(event_class_id) for event_class_id in CLASS_ROSTER]))

    assert {row.valence for row in loaded} == {None}
    assert {row.valence_reason for row in loaded} == {
        NullReason.CLASS_POLARITY_NOT_DECLARED_UPSTREAM.value
    }


def test_loader_rejects_a_partial_roster_instead_of_emitting_a_smaller_universe():
    conn = Connection([_row(event_class_id) for event_class_id in CLASS_ROSTER[:-1]])

    try:
        load_event_ontology(conn)
    except ValueError as error:
        assert "missing" in str(error)
    else:
        raise AssertionError("partial ontology must not be served")
