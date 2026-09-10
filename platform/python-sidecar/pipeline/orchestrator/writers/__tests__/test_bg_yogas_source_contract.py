"""Regression coverage for migration-434 detector yogas in the writer source."""

import pytest

from brahmagyan import l0_yogas
from brahmagyan.l0_yogas import DETECTOR_YOGAS, YOGAS_CORE
from pipeline.orchestrator.writers import ContextSpec
from pipeline.orchestrator.writers import bg_yogas as bg_yogas_writer


def test_detector_yogas_are_writer_owned_and_identity_disjoint() -> None:
    detector_ids = {yoga["canonical_id"] for yoga in DETECTOR_YOGAS}
    core_ids = {yoga["canonical_id"] for yoga in YOGAS_CORE}

    assert len(YOGAS_CORE) == 144
    assert len(DETECTOR_YOGAS) == 4
    assert detector_ids == {
        "dhana_yoga_house_lords",
        "raja_yoga_kendra_trikona",
        "sarasvati_yoga",
        "vipareeta_raja_yoga",
    }
    assert detector_ids.isdisjoint(core_ids)


def test_source_chunk_links_accept_only_real_uuid_identifiers() -> None:
    helper = getattr(l0_yogas, "_validated_source_chunk_ids", None)
    assert callable(helper), "typed yoga source-link validator is missing"

    exact_id = "11111111-1111-1111-1111-111111111111"
    assert helper({"_chunk_id_str": exact_id}) == [exact_id]
    assert helper({}) == []
    with pytest.raises(ValueError, match="source chunk"):
        helper({"_chunk_id_str": "same-chapter-guess"})


def test_writer_checks_projection_and_source_link_counts(monkeypatch) -> None:
    monkeypatch.setattr(l0_yogas, "extract_yogas_from_corpus", lambda _conn: [])
    expected = len(YOGAS_CORE) + len(DETECTOR_YOGAS)

    class Cursor:
        rowcount = 1

        def __init__(self, owner): self.owner = owner
        def __enter__(self): return self
        def __exit__(self, *_exc): return False
        def execute(self, sql, params=None): self.owner.sql.append(" ".join(sql.split()))
        def fetchone(self):
            return {"catalog_count": expected, "ontology_count": expected,
                    "reference_count": expected, "source_link_count": 0}

    class Conn:
        def __init__(self): self.sql = []
        def cursor(self): return Cursor(self)

    conn = Conn()
    result = l0_yogas.seed_yogas(conn, autocommit=False)
    assert any("AS source_link_count" in sql for sql in conn.sql)
    assert result["source_links_inserted"] == 0
    assert result["total_rows"] == expected * 3


@pytest.mark.parametrize("dry_run", [False, True])
def test_writer_result_counts_all_owned_projections(monkeypatch, dry_run: bool) -> None:
    monkeypatch.setattr(
        bg_yogas_writer,
        "seed_yogas",
        lambda *_args, **_kwargs: {
            "catalog_inserted": 233,
            "ontology_inserted": 233,
            "ref_inserted": 233,
            "source_links_inserted": 85,
            "inline_count": 144,
            "detector_count": 4,
            "extracted_count": 85,
            "warnings": [],
        },
    )

    result = bg_yogas_writer.YogasWriter().run(ContextSpec(
        asset_id="bg_yogas",
        build_id="build",
        db_conn=object(),
        dry_run=dry_run,
    ))

    assert result.rows_inserted == 784
    assert "source_links=85" in result.notes
    assert "total_owned=784" in result.notes
