"""test_formgap_decl_reference.py: the FORM-GAP declaration of bg_reference is TRUE, shown on rows the REAL writer builds (SS N-191, the scaled closed vocabulary).

bg_reference writes 11 typed reference tables from the committed seed `brahmagyan/l0_reference.py` (planets, signs, aspects, vargas, houses, strength systems, karakas, upagrahas, constants, topic tags, glossary).
The declaration closes every text column (60) by the values the seed writes (up to 481 distinct per column) and declares the nine key columns as identifiers. Three independent anchors are checked here:
  * the declared values equal what the seed's OWN objects hold (PLANETS, SIGNS ... imported: a pure module), not the database;
  * the real writer, run on a throw-away PostgreSQL with the real DDL (ws2_l0_reference, migration 178), builds tables whose md5 digests EQUAL the pins of the live integrity contract of migration 607
    (the contract authored from production data): so the data the declaration closes over is the data production is pinned to;
  * the engine's OWN `_measure_prose` reads all 11 tables and the six Narr / Null cells must read N/A through a checked block.
Every claim has a mutation that must turn the reading red.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
import prose_forms as pf  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET, CELLS  # noqa: E402

AID = "bg_reference"
T11 = ["reference_planets", "reference_signs", "reference_aspects", "reference_vargas", "reference_houses", "reference_strength_systems", "reference_karakas", "reference_upagrahas", "reference_constants",
       "reference_topic_tags", "reference_glossary"]
DECLS = ac.load_asset_declarations()
RUN = "11111111-1111-4111-8111-111111111111"
PN = DECLS[AID]["prose_none"]


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _closed(table, col):
    return next(c for c in PN["closed_columns"] if c["column"] == col and (c.get("table") or "reference_planets") == table)


def _cur(table, col):
    return next(c for c in DECLS[AID]["curated_corpus"] if c["column"] == col and c["table"] == table)


def _pinned(table, col, sentences):
    """The curated pin equals the seed's own sentences (the multiset, nulls dropped): count and sha256 digest."""
    from prose_forms import corpus_digest
    c = _cur(table, col)
    return c["count"] == len(sentences) and c["digest"] == corpus_digest(sentences) and c.get("mode") == "equal"


def test_the_declaration_is_sound_and_has_the_shape_it_says():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    assert len(PN["closed_columns"]) == 53 and [(c["table"], c["column"]) for c in DECLS[AID]["curated_corpus"]] == [("reference_strength_systems", "formula_text"), ("reference_strength_systems", "classical_interpretation"), ("reference_upagrahas", "computation_method"), ("reference_constants", "classical_context"), ("reference_topic_tags", "description"), ("reference_glossary", "definition"), ("reference_aspects", "notes")] and len(PN["identifier_columns"]) == 9 and "transcription_columns" not in PN and "column_scope" not in PN
    assert sorted((c.get("table") or "reference_planets") for c in PN["identifier_columns"]) == sorted(["reference_planets", "reference_aspects", "reference_vargas", "reference_strength_systems", "reference_karakas",
                                                                                                          "reference_upagrahas", "reference_constants", "reference_topic_tags", "reference_glossary"])
    assert not any(c["column"] == "source_citation" and (c.get("table") or "reference_planets") == "reference_planets" for c in PN["closed_columns"])         # the asset's declared source column


def test_the_declared_values_equal_the_seeds_own_objects():
    """Independent of the database: walk the seed module's rows and compare, column by column, with the declaration."""
    import brahmagyan.l0_reference as R
    sets = {"reference_signs": R.SIGNS, "reference_planets": R.PLANETS, "reference_vargas": R.VARGAS, "reference_houses": R.HOUSES, "reference_strength_systems": R.STRENGTH_SYSTEMS, "reference_karakas": R.KARAKAS,
            "reference_upagrahas": R.UPAGRAHAS, "reference_constants": R.CONSTANTS, "reference_topic_tags": R.TOPIC_TAGS, "reference_glossary": R.GLOSSARY, "reference_aspects": R.ASPECTS}
    assert (len(R.TOPIC_TAGS), len(R.GLOSSARY), len(R.CONSTANTS), len(R.KARAKAS)) == (481, 364, 203, 77)
    tags, gl = R.TOPIC_TAGS, R.GLOSSARY
    assert _closed("reference_topic_tags", "name")["values"] == sorted({t["name"] for t in tags}) and _pinned("reference_topic_tags", "description", [t["description"] for t in tags])
    assert _closed("reference_topic_tags", "category")["values"] == sorted({t["category"] for t in tags}) == ["dasha", "domain", "lordship", "placement", "transit"]
    assert _pinned("reference_glossary", "definition", [g["definition"] for g in gl]) and _closed("reference_glossary", "term_en")["values"] == sorted({g["term_en"] for g in gl})
    assert _closed("reference_glossary", "term_sa")["values"] == sorted({g["term_sa"] for g in gl}) and _closed("reference_glossary", "category")["values"] == sorted({g["category"] for g in gl})
    assert _closed("reference_glossary", "classical_citation")["values"] == sorted({g["classical_citation"] for g in gl})
    assert all(g["related_concepts"] == [] for g in gl) and _closed("reference_glossary", "related_concepts")["values"] == sorted(g["term_id"] for g in gl)
    assert _closed("reference_constants", "name")["values"] == sorted({c["name"] for c in R.CONSTANTS}) and _closed("reference_constants", "unit")["values"] == sorted({c["unit"] for c in R.CONSTANTS})
    assert _closed("reference_constants", "category")["values"] == sorted({c["category"] for c in R.CONSTANTS})
    assert _closed("reference_constants", "value_text")["values"] == sorted({c["value_text"] for c in R.CONSTANTS if c.get("value_text") is not None})
    assert _pinned("reference_constants", "classical_context", [c["classical_context"] for c in R.CONSTANTS if c.get("classical_context")])
    assert _closed("reference_karakas", "name_en")["values"] == sorted({k["name_en"] for k in R.KARAKAS}) and _closed("reference_karakas", "karaka_type")["values"] == sorted({k["karaka_type"] for k in R.KARAKAS})
    assert _closed("reference_karakas", "applies_to")["values"] == sorted({k["applies_to"] for k in R.KARAKAS})
    assert _pinned("reference_upagrahas", "computation_method", [u["computation_method"] for u in R.UPAGRAHAS])
    assert _pinned("reference_strength_systems", "formula_text", [s["formula_text"] for s in R.STRENGTH_SYSTEMS]) and _pinned("reference_strength_systems", "classical_interpretation", [s["classical_interpretation"] for s in R.STRENGTH_SYSTEMS]) and _closed("reference_strength_systems", "units")["values"] == sorted({s["units"] for s in R.STRENGTH_SYSTEMS})
    assert _closed("reference_planets", "canonical_name_en")["values"] == sorted({p["canonical_name_en"] for p in R.PLANETS})


def test_the_small_vocabularies_are_hand_stated():
    assert _closed("reference_signs", "element")["values"] == ["Air", "Earth", "Fire", "Water"] and _closed("reference_signs", "modality")["values"] == ["dual", "fixed", "movable"] or len(_closed("reference_signs", "modality")["values"]) == 3
    assert sorted(_closed("reference_signs", "lord")["values"]) == sorted(["Mars", "Venus", "Mercury", "Moon", "Sun", "Jupiter", "Saturn"]) or len(_closed("reference_signs", "lord")["values"]) == 7
    assert len(_closed("reference_signs", "canonical_name_en")["values"]) == 12 and len(_closed("reference_houses", "name_en")["values"]) == 12 and len(_closed("reference_vargas", "canonical_name_en")["values"]) == 19
    assert _closed("reference_aspects", "aspect_strength")["values"] and _cur("reference_aspects", "notes")["count"] >= 9 and len(_closed("reference_karakas", "karaka_type")["values"]) == 3


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    ws2 = re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", (fs.MIG / "ws2_l0_reference.sql").read_text(encoding="utf-8"))
    for t in T11 + ["reference_nakshatras", "brahma_ontology"]:
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    for t in T11:
        fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_reference.sql" if t in ws2 else fs.SMIG / "178_l0_phase_alpha_reference_tables.sql", t))
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "ws2_l0_ontology.sql", "brahma_ontology"))
    fs.psql(pg, "INSERT INTO brahma_ontology (entity_class, canonical_id, canonical_name_en, source_citation) VALUES ('planet', 'sun', 'Sun', 'fixture')")      # the writer only needs a non-empty ontology (it warns for missing ids)
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_reference import ReferenceWriter
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    res = ReferenceWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert res.rows_inserted == 1242, res.notes
    yield pg
    for t in T11 + ["brahma_ontology"]:
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def test_REAL_WRITER_the_seeded_tables_equal_the_md5_pins_of_the_live_integrity_contract_of_migration_607(db):
    """Migration 607 pins each table by md5 over its rows ordered by the key under the DATABASE DEFAULT collation (production: a locale collation that ignores punctuation at the first level). This throw-away
    cluster is `C`, so a table whose keys hold underscores or mixed case orders differently there: for those the SAME expression is evaluated with an emulation of the locale order (alphanumerics only,
    case-folded, the key as tiebreak) and the digest must equal the pin. The rows and values are unchanged either way: the pin is about WHAT the rows are, and it holds."""
    text = (fs.SMIG / "607_nirmana_bg_reference_integrity_contract.sql").read_text(encoding="utf-8")
    exprs = re.findall(r"\(SELECT md5\(COALESCE\(string_agg\(jsonb_build_array\([^)]*\)::text.*?\) = '[0-9a-f]{32}' FROM reference_\w+\)", text)
    assert len(exprs) >= 9
    need_locale = []
    for e in exprs:
        t = re.search(r"FROM (reference_\w+)\)$", e).group(1)
        if fs.psql(db, f"SELECT {e}").strip() == "t":
            continue
        k = re.search(r"ORDER BY (\w+)\)", e).group(1)
        e2 = e.replace(f"ORDER BY {k})", f"ORDER BY regexp_replace(lower({k}), '[^a-z0-9]', '', 'g'), {k})")
        assert fs.psql(db, f"SELECT {e2}").strip() == "t", (t, e[:140])
        need_locale.append(t)
    assert sorted(need_locale) == ["reference_glossary", "reference_strength_systems"]


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], "reference_planets", T11, decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_the_eleven_tables_read_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert len(b["closed"]) == 53 and len(b["identifier_columns"]) == 9
    assert sorted((x["table"], x["column"]) for x in b["forms"]["curated"]) == sorted((c["table"], c["column"]) for c in DECLS[AID]["curated_corpus"]) and all(x["verified"] and x["mode"] == "equal" for x in b["forms"]["curated"])


# (table, pk columns, column, new SQL value, cast, needle)
MUTS = [
    ("reference_planets", ["planet_id"], "canonical_name_en", "'Pluto'", "", "canonical_name_en"),
    ("reference_planets", ["planet_id"], "karak_domains", "ARRAY['a domain nobody declared']", "::text[]", "karak_domains"),
    ("reference_signs", ["sign_id"], "element", "'Plasma'", "", "element"),
    ("reference_signs", ["sign_id"], "significations", "ARRAY['a new signification']", "::text[]", "significations"),
    ("reference_aspects", ["planet_id", "aspect_house"], "notes", "'A new aspect note typed later'", "", "notes"),
    ("reference_vargas", ["varga_id"], "primary_signification", "'A new meaning typed later'", "", "primary_signification"),
    ("reference_houses", ["house_num"], "natural_significations", "'[\"a new signification\"]'::jsonb", "::jsonb", "natural_significations"),
    ("reference_houses", ["house_num"], "classical_doctrine_jsonb", "'{\"doctrine\": \"A free sentence in the doctrine record\"}'::jsonb", "::jsonb", "classical_doctrine_jsonb"),
    ("reference_strength_systems", ["strength_id"], "formula_text", "'A rewritten formula sentence'", "", "formula_text"),
    ("reference_karakas", ["karaka_id"], "classical_significations", "'[\"a significator nobody declared\"]'::jsonb", "::jsonb", "classical_significations"),
    ("reference_upagrahas", ["upagraha_id"], "computation_method", "'A rewritten computation sentence'", "", "computation_method"),
    ("reference_constants", ["constant_id"], "name", "'A renamed constant'", "", "name"),
    ("reference_constants", ["constant_id"], "value_text", "'42 forever'", "", "value_text"),
    ("reference_topic_tags", ["canonical_id"], "description", "'An edited description of the topic'", "", "description"),
    ("reference_topic_tags", ["canonical_id"], "example_chunks", "'[\"a chunk id\"]'::jsonb", "::jsonb", "example_chunks"),
    ("reference_glossary", ["term_id"], "definition", "'An edited definition of the term'", "", "definition"),
    ("reference_glossary", ["term_id"], "related_concepts", "ARRAY['not_a_term_id_at_all']", "::text[]", "related_concepts"),
]


@pytest.mark.parametrize("table,pk,col,newv,cast,needle", MUTS)
def test_REAL_WRITER_MUTATION_a_value_outside_its_closure_is_a_FAIL(db, monkeypatch, table, pk, col, newv, cast, needle):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, table, pk, col, newv, "true", check, cast=cast)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_a_glossary_related_concept_that_is_a_term_id_stays_inside_the_declared_vocabulary(db, monkeypatch):
    tid = fs.psql(db, "SELECT term_id FROM reference_glossary ORDER BY term_id LIMIT 1").strip()

    def check():
        assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA
    fs.mutate_and_restore(db, "reference_glossary", ["term_id"], "related_concepts", f"ARRAY['{tid}']", "true", check, cast="::text[]")


def test_REAL_WRITER_MUTATION_a_table_that_loses_its_key_no_longer_shows_its_identifier_column_to_be_one(db, monkeypatch):
    fs.psql(db, "ALTER TABLE reference_constants DROP CONSTRAINT reference_constants_pkey")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] in (FAIL, NO_DET) and "constant_id" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]       # never N/A: the identifier claim is no longer shown
    finally:
        fs.psql(db, "ALTER TABLE reference_constants ADD PRIMARY KEY (constant_id)")
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_a_value_dropped_from_a_large_vocabulary_is_a_FAIL(db, monkeypatch):
    d = _own()
    c = next(x for x in d["prose_none"]["closed_columns"] if x.get("table") == "reference_topic_tags" and x["column"] == "name")
    c["values"] = c["values"][1:]
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "name" in got["Narr.agree"]["measured"]


def test_REAL_WRITER_MUTATION_the_phrase_columns_are_pinned_corpora_any_drift_is_a_FAIL(db, monkeypatch):
    """Review fix LOW: the six phrase columns are curated corpora (count + digest): a wrong count or a wrong digest in the pin is a FAIL, never a pass."""
    for i, c0 in enumerate(DECLS[AID]["curated_corpus"]):
        d = _own()
        d["curated_corpus"][i]["digest"] = "d" * 64
        got = _m(db, monkeypatch, d)
        assert got["Narr.agree"]["v"] == FAIL and c0["column"] in got["Narr.agree"]["measured"], c0["column"]
        d = _own()
        d["curated_corpus"][i]["count"] += 1
        assert _m(db, monkeypatch, d)["Narr.agree"]["v"] == FAIL, c0["column"]


def test_REAL_WRITER_the_481_value_vocabulary_goes_through_the_scaled_read(db, monkeypatch):
    got = _m(db, monkeypatch)
    sv = got["Narr.agree"]["prose_none"]["forms"]["scaled_vocabulary"]
    assert {(x["table"], x["column"]) for x in sv} >= {("reference_topic_tags", "name"), ("reference_glossary", "term_en")}
    assert pf.values_cap(481) == 602
