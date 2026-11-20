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
        def fetchall(self): return []   # attribution_state capture (SS N-111): no row carries a state in this fake
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


# ── WFIX-A / CLAUDE.md N.7 item 6: an honest value beats an invented fallback sentence ───────────────

def test_formation_text_never_invents_a_formation_per_verse_sentence() -> None:
    rule = {"requires": [{"planets_in": ["1", "7"]}], "derivation": "structured_template"}
    # a verbatim clause always wins
    assert l0_yogas._formation_text("Planets occupy the 1st and 7th.", rule) == "Planets occupy the 1st and 7th."
    # no clause: a deterministic restatement of the row's OWN cited rule, never prose about a verse
    fallback = l0_yogas._formation_text("", rule)
    assert fallback == 'Structured formation rule: {"derivation": "structured_template", "requires": [{"planets_in": ["1", "7"]}]}'
    assert "formation per" not in fallback


def test_signification_text_never_presents_the_yoga_name_as_its_signification() -> None:
    assert l0_yogas._signification_text("Gives wealth.", "clause") == "Gives wealth."
    assert l0_yogas._signification_text("", "A verbatim defining clause.") == "A verbatim defining clause."
    assert l0_yogas._signification_text("", "") == ""      # NOT NULL column: honest empty, not the name


def test_corpus_extraction_emits_no_invented_sentence_for_a_clauseless_template_yoga() -> None:
    """vajra_sar / yava_sar / vapi_sar were written with formation_text='<name>: formation per PG358:C1
    (bphs Ch.358)' and significations_text='<name>' when the chunk named the yoga without a clause."""
    chunk = {"id": "11111111-1111-1111-1111-111111111111", "text_id": "bphs", "chapter": 358,
             "verse_ref": "PG358:C1", "content_en": "The Vajra yoga is named in this passage.",
             "tradition_school": "parashari"}

    class Cursor:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def execute(self, *_a, **_k): pass
        def fetchall(self): return [chunk]

    class Conn:
        def cursor(self, *a, **k): return Cursor()

    rows = {r["canonical_id"]: r for r in l0_yogas.extract_yogas_from_corpus(Conn())}
    row = rows["vajra_sar"]
    assert "formation per" not in row["formation_text"]
    assert row["formation_text"].startswith("Structured formation rule: ")
    assert row["significations_text"] != row["name_en"]
    assert row["significations_text"] == ""


def test_empty_signification_seeds_a_null_ontology_description_not_an_empty_string(monkeypatch) -> None:
    """brahma_ontology.description is nullable: a yoga whose chunk states no result gets NULL, the
    honest value, not '' (and never the yoga's name -- the pre-WFIX-A fallback)."""
    extracted = {
        "canonical_id": "vajra_sar", "name_sa": "Vajra Yoga (Saravali)", "name_en": "Vajra Yoga (Saravali) Yoga",
        "category": "other", "school": "parashari",
        "formation_rule_jsonb": {"requires": [{"relation": "benefics_in_1_7_malefics_in_4_10"}]},
        "formation_text": 'Structured formation rule: {"requires": [{"relation": "benefics_in_1_7_malefics_in_4_10"}]}',
        "significations_jsonb": {"gives": [], "subcategory": "structured_template", "source_chunk": "c"},
        "significations_text": "", "cancellation_conditions": {}, "classical_citations": [{"text_id": "bphs"}],
        "rare": False, "source_citation": "BPHS Ch.358 (PG358:C1)",
        "_chunk_id_str": "11111111-1111-1111-1111-111111111111",
    }
    monkeypatch.setattr(l0_yogas, "extract_yogas_from_corpus", lambda _conn: [extracted])
    expected = len(YOGAS_CORE) + len(DETECTOR_YOGAS) + 1

    class Cursor:
        rowcount = 1

        def __init__(self, owner): self.owner = owner
        def __enter__(self): return self
        def __exit__(self, *_exc): return False
        def execute(self, sql, params=None): self.owner.calls.append((" ".join(sql.split()), params))
        def fetchone(self):
            return {"catalog_count": expected, "ontology_count": expected,
                    "reference_count": expected, "source_link_count": 1}

    class Conn:
        def __init__(self): self.calls = []
        def cursor(self): return Cursor(self)

    conn = Conn()
    l0_yogas.seed_yogas(conn, autocommit=False)
    onto = [p for s, p in conn.calls if s.startswith("INSERT INTO brahma_ontology") and p[0] == "vajra_sar"]
    assert len(onto) == 1
    assert onto[0][4] is None                      # description
    other = [p for s, p in conn.calls if s.startswith("INSERT INTO brahma_ontology") and p[0] != "vajra_sar"]
    assert all(isinstance(p[4], str) and p[4] for p in other)     # inline yogas keep their [:150] description
