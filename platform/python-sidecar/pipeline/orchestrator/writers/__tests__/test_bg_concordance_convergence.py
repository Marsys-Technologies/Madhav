"""Regression coverage for the global bg_concordance replacement contract."""

from __future__ import annotations

from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers.bg_concordance import ConcordanceWriter


class _Cursor:
    def __init__(self, connection: "_Connection") -> None:
        self.connection = connection
        self._rows: list[dict] = []
        self.rowcount = 0

    def __enter__(self) -> "_Cursor":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, sql: str, params: tuple | None = None) -> None:
        normalized = " ".join(sql.split())
        self.rowcount = 0

        if normalized == "SELECT canonical_id, name, category FROM reference_topic_tags":
            self._rows = [
                {"canonical_id": "topic_a", "name": "Canonical topic", "category": "house_lord"}
            ]
        elif normalized.startswith("SELECT COUNT(*) AS count FROM classical_text_chunks"):
            self._rows = [{"count": 2}]
        elif normalized.startswith("SELECT topic_tag, text_id, COUNT(*) AS n_chunks"):
            self._rows = [{"topic_tag": "topic_a", "text_id": "bphs", "n_chunks": 2}]
        elif normalized == "SELECT rule_id::text, text_id FROM sutravali_rules":
            self._rows = [
                {"rule_id": "00000000-0000-0000-0000-000000000001", "text_id": "bphs"}
            ]
        elif normalized == "DELETE FROM classical_attributions":
            self.rowcount = len(self.connection.attributions)
            self.connection.attributions.clear()
            self._rows = []
        elif normalized.startswith("INSERT INTO classical_attributions"):
            assert params is not None
            key = (params[0], params[3])
            if key not in self.connection.attributions:
                self.connection.attributions[key] = {
                    "topic_canonical_name": params[1],
                    "topic_category": params[2],
                    "source_text_ids": params[4],
                    "rule_ids": params[5],
                    "match_method": params[6],
                    "match_confidence": params[7],
                }
                self.rowcount = 1
            self._rows = []
        elif normalized == "SELECT COUNT(*) AS count FROM classical_attributions":
            self._rows = [{"count": len(self.connection.attributions)}]
        elif normalized == "SELECT COUNT(DISTINCT topic_id) AS count FROM classical_attributions":
            self._rows = [{"count": len({key[0] for key in self.connection.attributions})}]
        elif normalized == "SELECT COUNT(DISTINCT school) AS count FROM classical_attributions":
            self._rows = [{"count": len({key[1] for key in self.connection.attributions})}]
        else:
            raise AssertionError(f"unexpected SQL: {normalized}")

    def fetchall(self) -> list[dict]:
        return self._rows

    def fetchone(self) -> dict:
        return self._rows[0]


class _Connection:
    def __init__(self) -> None:
        self.attributions = {
            ("topic_a", "parashari"): {
                "topic_canonical_name": "stale name",
                "topic_category": "stale category",
                "source_text_ids": "{stale_text}",
                "rule_ids": "{}",
                "match_method": "stale",
                "match_confidence": 0.2,
            },
            ("obsolete_topic", "parashari"): {
                "topic_canonical_name": "obsolete",
            },
        }

    def cursor(self) -> _Cursor:
        return _Cursor(self)


def test_writer_replaces_stale_and_accreted_rows() -> None:
    connection = _Connection()
    result = ConcordanceWriter().run(ContextSpec(
        asset_id="bg_concordance",
        build_id="convergence-regression",
        db_conn=connection,
    ))

    assert result.rows_inserted == 1
    assert result.rows_skipped == 0
    assert set(connection.attributions) == {("topic_a", "parashari")}
    assert connection.attributions[("topic_a", "parashari")] == {
        "topic_canonical_name": "Canonical topic",
        "topic_category": "house_lord",
        "source_text_ids": '{"bphs"}',
        "rule_ids": "{00000000-0000-0000-0000-000000000001}",
        "match_method": "topic_tag",
        "match_confidence": 0.4,
    }
