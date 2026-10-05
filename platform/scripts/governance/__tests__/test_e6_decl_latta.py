"""test_e6_decl_latta.py: DECL-LATTA (Suvarna engine campaign, first asset toward the first real certificate).

bg_phaladeepika_latta's entry in asset_declarations.json (1.10.0) declares THREE reviewed blocks, built on the shapes S2 / S3 verified:
  * carriage: D1 (transcription), citation_state sourced_ocr_unverified, both chunk ids, the Sloka 42-44 span, the four anchor phrases of the
    affliction sentence, the per-claimant {clause, effect} pairs side by side (the passage is read from classical_text_chunks by span and is
    NEVER copied into the declaration);
  * vocab_alias: planet class on `graha`, identity_only (the table carries no alias column);
  * ldgr_source: `verse_ref` (accurate: Adh.XXVI PG338-339 Sloka 42-44) at sourced_ocr_unverified. The per-row `source_citation` names PG339 only
    (a recorded finding, to be corrected at the next writer change).
At 1.10.0 it declared NO null_convention; 1.11.0 (DECL-LATTA-NULL, test_e6_decl_latta_null.py) adds it, with created_at as a stamp column and NO created_at constant
(all 8 rows share one write timestamp). The cells measured HERE are Carr, Vocab and Ldgr; Narr x4, Earn.build_record and Dens are unchanged.

Part 1 is offline (validator + pure detectors, seeded defects). Part 2 runs the REAL detectors on a disposable Postgres built from the corpus
export (8 rows + both chunks; the committed fixture + the three known constant columns where the export file is absent, e.g. CI) and a
seeded 11-entity planet class."""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import _decl_version  # noqa: E402
import carriage_d1 as d1  # noqa: E402
import test_e6_s2_carriage as s2  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

AID = "bg_phaladeepika_latta"
BATCH2_VOCAB = ["bg_dignity_reference", "bg_kp_sublord_division", "bg_transit_engine", "bg_transit_rules", "bg_vastu_directions"]      # declared by L0-WAVE batch 2
PASS, FAIL, PARTIAL, NO_DET, NA = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.NA
DECL = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
ENTRY = DECL["assets"][AID]
CAR, VA, LS = ENTRY["carriage"], ENTRY["vocab_alias"], ENTRY["ldgr_source"]
SPEC = CAR["spec"]
IDS = ["phaladeepika_pg0338_c01", "phaladeepika_pg0339_c01"]
COLS = ["table_version", "graha", "count_from_graha", "direction", "effect_description", "affliction_condition", "source_citation", "verse_ref",
        "created_at"]
CORPUS_FILE = pathlib.Path("/Users/Dev/suvarna-evidence/engine/corpus/phaladeepika_latta_corpus_fixtures_v2.json")
SAVED = pathlib.Path("/Users/Dev/suvarna-evidence/census_fresh/1e5781a")
ONTOLOGY = ["ascendant", "jupiter", "ketu", "mars", "mercury", "midheaven", "moon", "rahu", "saturn", "sun", "venus"]   # the 11 planet-class entities
PG339 = ("[HIGH] Phaladeepika — Trans. V. Subrahmanya Sastri, 2nd Ed. 1950 (archive.org: Phaladeepika2ndEd.1950ByVSubrahmanyaSastri) | PG339")


def _data():
    """(chunks, rows, source): the corpus export when present, else the committed fixture plus the three constant columns the export holds."""
    if CORPUS_FILE.exists():
        d = json.loads(CORPUS_FILE.read_text(encoding="utf-8"))
        return d["classical_text_chunks"], d["bg_phaladeepika_latta"], "corpus-export"
    fx = s2.FX
    rows = [dict(r, table_version="phaladeepika_vedha_v01", source_citation=PG339, created_at="2026-08-02T05:18:29.576273+00:00") for r in fx["bg_phaladeepika_latta"]]
    return fx["classical_text_chunks"], rows, "committed-fixture"


CHUNK_LIST, ROWS, SOURCE = _data()
CHUNKS = {c["chunk_id"]: c for c in CHUNK_LIST}


def _reasons(x):
    """Every `why` / `means` / `identity_only_why` string of an entry (the prose the review reads; structural words such as mode `exactly` are not prose)."""
    out = []
    if isinstance(x, dict):
        for k, v in x.items():
            out += [v] if k in ("why", "means", "identity_only_why") and isinstance(v, str) else _reasons(v)
    elif isinstance(x, list):
        for v in x:
            out += _reasons(v)
    return out


def _doc(mutate):
    d = copy.deepcopy(DECL)
    mutate(d["assets"][AID])
    return d


def _refused(mutate, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(mutate))


# ───────────────────────── Part 1: the committed entry ─────────────────────────

def test_the_committed_file_is_1_10_0_and_the_validator_accepts_this_entry():
    assert DECL["version"] == _decl_version.CURRENT and "bg_phaladeepika_latta" in DECL["description"].split("Version 1.10.0", 1)[1]      # 1.11.0 DECL-LATTA-NULL, 1.12.0 NARR-GUARD
    ac.validate_declarations(DECL)
    assert ac.load_asset_declarations()[AID]["carriage"]["applies"] == "D1"


L0_FILL_NO_ALIAS_CLASS = ["bg_compendium_index", "bg_formula_constants", "bg_ghatana", "bg_gochara_citation_resolution", "bg_kota_chakra_rings", "bg_muhurta_lattice", "bg_text_index", "bg_texts", "bg_vedha_malefic_scale", "bg_vidhi_floors", "bg_vidhi_primitives", "bo_chart_gestalt", "bo_drishti", "bo_grounding", "bo_pramana_mapa", "bo_samskara", "bo_karanajala", "bo_anveshana"]      # E5.7 L0 fills: `na: no_alias_class` for 11 more assets (no carriage, no ldgr_source)


def test_this_asset_alone_declares_the_three_blocks_and_its_created_at_is_a_stamp_never_a_constant():
    decl = [a for a, e in DECL["assets"].items() if any(k in (e.get("carriage") or {}) for k in ac.CARRIAGE_DECL_FIELDS) or "vocab_alias" in e or "ldgr_source" in e]
    assert {AID, *BATCH2_VOCAB, *L0_FILL_NO_ALIAS_CLASS} <= set(decl)                  # L0-WAVE batch 2 vocab_alias declarers (N-156: the carriage fill adds the 82 L0-L2 assets as carriage declarers)
    assert [a for a, e in DECL["assets"].items() if "ldgr_source" in e] == [AID]
    assert len([a for a, e in DECL["assets"].items() if any(k in (e.get("carriage") or {}) for k in ac.CARRIAGE_DECL_FIELDS)]) == 82
    assert [a for a, e in DECL["assets"].items() if "null_convention" in e] == [AID]                  # DECL-LATTA-NULL (1.11.0)
    nc = ENTRY["null_convention"]
    assert "created_at" not in [c["column"] for c in nc["constants"]]            # option A is refused: no created_at constant; it is a declared stamp column
    assert [c["column"] for c in nc["stamp_columns"]] == ["created_at"]
    hits = []

    def walk(x, path):
        if isinstance(x, str) and "created_at" in x:
            hits.append(path)
        elif isinstance(x, dict):
            [walk(v, f"{path}.{k}") for k, v in x.items()]
        elif isinstance(x, list):
            [walk(v, f"{path}[{i}]") for i, v in enumerate(x)]
    walk(ENTRY, "entry")
    assert "entry.null_convention.stamp_columns[0].column" in hits and all(h.startswith("entry.null_convention.stamp_columns[0].") for h in hits), hits   # created_at only ever under stamp_columns


def test_the_entry_declares_what_the_strategist_ruled():
    assert CAR["nature"] == "transcription" and CAR["applies"] == "D1" and CAR["citation_state"] == "sourced_ocr_unverified"
    assert CAR["served_surface"] is None                                 # unchanged
    assert "anchor-matched, OCR-repaired" in CAR["why"]
    for needle in ("ENGLISH translation only", "not checked against the printed book", "text_id-prefixed preimage", "bare preimage", "Mars and Saturn",
                   "reserved empty", "Ketu has no row"):                       # the ruling's mandatory statements are pinned
        assert needle in CAR["why"], needle
    assert "OCR-garbled" in LS["why"] and "Slokas 45-46" in LS["why"] and "no detector checks the sloka label" in LS["why"] and "PG339 only" in LS["why"]
    new_sentence = DECL["description"].split("Version 1.10.0", 1)[1].split(" REGISTRY_REVISION 15", 1)[0]   # the 1.10.0 sentence only (a later pin appends its own)
    whole = json.dumps(ENTRY, ensure_ascii=False).lower()                         # the WHOLE entry JSON, not only its prose strings
    assert whole.count("exactly") == 1 and '"mode": "exactly"' in whole           # 'exactly' appears only as the null_convention scope mode value
    whole = whole.replace('"mode": "exactly"', '"mode": "scope"')
    next_sentence = DECL["description"].split("Version 1.11.0", 1)[1]
    texts = [" ".join(_reasons(ENTRY)).lower(), new_sentence.lower(), whole, next_sentence.lower()]   # every why, the whole entry, the 1.10.0 and 1.11.0 description sentences
    for word in ("verbatim", "accurate", "exact"):
        assert not any(word in t for t in texts), word
    assert "read from classical_text_chunks by span; only the declared clause/condition strings are quoted" in new_sentence
    assert "never copied in" not in new_sentence
    stale = DECL["description"]
    assert "No asset declares one yet: an asset without it reads exactly as before. Version 1.8.0" not in stale and "No asset declares either yet" not in stale
    assert SPEC["chunk_ids"] == IDS and SPEC["span"] == {"start": "Sloka 42-44"} and SPEC["table"] == AID and SPEC["expected_rows"] == 8
    ef = {e["column"]: e for e in SPEC["extra_fields"]}
    assert ef["affliction_condition"]["anchors"] == ["when thus counting", "natal star", "Latta star", "sickness and anguish"]
    assert ef["verse_ref"] == {"column": "verse_ref", "kind": "equals", "value": "Adh.XXVI PG338-339 Sloka 42-44"}
    # clauses side by side: each claimant carries {clause, effect}; Mars and Saturn (reserved-NULL effect) have none; Ketu has no row at all
    assert sorted(SPEC["effect_clauses"]) == ["Jupiter", "Mercury", "Moon", "Rahu", "Sun", "Venus"]
    assert all(sorted(v) == ["clause", "effect"] for v in SPEC["effect_clauses"].values())
    assert VA["class"] == "planet" and VA["vocab_column"] == "graha" and VA["identity_only"] is True and "alias_column" not in VA
    assert "no alias" in VA["identity_only_why"] and "na" not in VA                         # no_alias_class does NOT apply
    assert LS["source_column"] == "verse_ref" and LS["citation_state"] == "sourced_ocr_unverified" and "na" not in LS


def test_the_committed_latta_entry_carries_its_prose_coupling_and_deleting_it_is_refused():
    """NARR-GUARD (N-94, review F1): prose_fields [] beside the D1 transcription carriage is valid only with the coupling to Carr.D1; the pin lives here as well as in test_e6_narr_guard.py."""
    assert ENTRY["prose_fields"] == [] and ENTRY["prose_coupling"]["to"] == "carriage_d1" and ENTRY["prose_coupling"]["columns"] == ["effect_description", "affliction_condition"]
    _refused(lambda e: e.pop("prose_coupling"), "prose_coupling is missing")


def test_the_passage_is_never_copied_into_the_declaration():
    blob = " ".join(CHUNKS[i]["content_en"] for i in IDS)
    seg = d1.cut_span(d1._ws(blob), SPEC["span"])[0]
    strings = []

    def walk(x):
        if isinstance(x, str):
            strings.append(x)
        elif isinstance(x, dict):
            [walk(v) for v in x.values()]
        elif isinstance(x, list):
            [walk(v) for v in x]
    walk(ENTRY)
    assert max(len(s) for s in strings) <= 1200 and not any(len(s) > 150 and d1._ws(s) in seg for s in strings)
    assert seg and d1._ws(" ".join(CHUNKS[i]["content_en"] for i in IDS)[:200]) not in d1._ws(json.dumps(ENTRY))


def test_each_declared_clause_is_one_whole_clause_of_the_passage_with_its_offsets():
    """The PR table (graha | clause | effect | passage excerpt with its offsets in chunk 0339): every clause is found exactly once, in chunk 0339."""
    c339 = CHUNKS[IDS[1]]["content_en"]
    spans = {}
    for g, v in SPEC["effect_clauses"].items():
        pat = r"\s+".join(re.escape(w) for w in v["clause"].split())
        hits = [m.span() for m in re.finditer(pat, c339)]
        assert len(hits) == 1 and not re.search(pat, CHUNKS[IDS[0]]["content_en"]), g
        spans[g] = hits[0]
    ordered = sorted(spans.values())
    assert all(a[1] <= b[0] for a, b in zip(ordered, ordered[1:]))                   # no two clauses overlap
    assert spans == {"Sun": (288, 351), "Rahu": (352, 404), "Jupiter": (406, 506), "Venus": (507, 550), "Mercury": (552, 624), "Moon": (626, 665)} or SOURCE != "corpus-export"


# ───────────────────────── Part 1b: seeded defects flip it (validator) ─────────────────────────

@pytest.mark.parametrize("block, field, bad, match", [
    ("carriage", "why", "", "carriage.why"), ("carriage", "why", " ", "carriage.why"),
    ("vocab_alias", "why", "", "vocab_alias.why"), ("vocab_alias", "why", "TBD placeholder text here", "placeholder"),
    ("vocab_alias", "identity_only_why", "", "identity_only_why"),
    ("ldgr_source", "why", "short", "ldgr_source.why"), ("ldgr_source", "why", "source note pending later review", "ldgr_source.why"),
    ("carriage", "evidence", "TBD", "carriage.evidence"), ("vocab_alias", "evidence", "TBD", "vocab_alias.evidence"),
    ("ldgr_source", "evidence", "TBD", "ldgr_source.evidence"),
    ("carriage", "evidence", "platform/python-sidecar/brahmagyan/no_such_file.py:1", "carriage.evidence"),
    ("vocab_alias", "evidence", "platform/supabase/migrations/no_such_migration.sql:1", "vocab_alias.evidence"),
    ("ldgr_source", "evidence", "platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:99999", "line 99999"),
    ("vocab_alias", "evidence", "unverified:", "evidence"),
])
def test_a_blank_placeholder_or_unreal_why_or_evidence_is_refused(block, field, bad, match):
    _refused(lambda e: e[block].__setitem__(field, bad), match)


def test_spec_evidence_pointers_must_exist():
    _refused(lambda e: e["carriage"]["spec"].__setitem__("effect_clauses_evidence", "platform/nope/no_such.json:1"), "effect_clauses_evidence")
    _refused(lambda e: e["carriage"]["spec"]["extra_fields"][0].__setitem__("condition_evidence", "platform/nope/no_such.json:1"), "condition_evidence")
    _refused(lambda e: e["carriage"]["spec"]["extra_fields"][0]["repairs"][0].__setitem__("evidence", "platform/nope/no_such.json:1"), "repairs")


def test_a_malformed_declaration_is_refused():
    _refused(lambda e: e["carriage"].__setitem__("citation_state", "verbatim"), "citation_state")
    _refused(lambda e: e["carriage"].__setitem__("applies", "D3"), "requires applies")
    _refused(lambda e: e["vocab_alias"].__setitem__("alias_column", "synonyms"), "identity_only")
    _refused(lambda e: e["vocab_alias"].__setitem__("class", "sign"), "alias class")
    _refused(lambda e: e["ldgr_source"].__setitem__("citation_state", "verbatim"), "citation_state")
    _refused(lambda e: e["ldgr_source"].__setitem__("na", "no_classical_claim"), "ldgr_source")        # N/A words do not apply to this asset
    _refused(lambda e: e["vocab_alias"].update(na="no_alias_class"), "vocab_alias")


def test_a_convention_without_the_stamp_declaration_would_fail_on_created_at_the_reason_it_is_declared_a_stamp():
    """History (option C, 1.10.0): the detector reads created_at, one value on all 8 rows, as an undeclared constant, so a convention WITHOUT a
    stamp declaration FAILs the Null cell (pure grader, below); 1.11.0 declares created_at as a stamp column instead (test_e6_decl_latta_null.py)."""
    assert "null_convention" in ENTRY
    stats = dict(rows=8, cols={c: dict(nulls=0, distinct=8, fallback=0) for c in COLS})
    for c in ("table_version", "affliction_condition", "source_citation", "verse_ref", "created_at"):
        stats["cols"][c] = dict(nulls=0, distinct=1, sole="x", fallback=0)
    stats["cols"]["direction"]["distinct"] = 2
    stats["cols"]["effect_description"] = dict(nulls=2, distinct=6, fallback=0, null_outside=0, null_outside_keys=[], nonnull_inside=0, nonnull_inside_keys=[])
    types = {c: "text" for c in COLS} | {"count_from_graha": "smallint", "created_at": "timestamp with time zone"}
    conv = dict(table=AID, nullable=[dict(column="effect_description", means="the passage gives no effect clause for this graha",
                                          scope=dict(key_column="graha", null_for=["Mars", "Saturn"], mode="exactly"))],
                constants=[dict(column=c, why="one shared value on every row") for c in ("table_version", "affliction_condition", "source_citation", "verse_ref")])
    r = ac.grade_null_convention(conv, COLS, types, stats)
    assert r["v"] == FAIL and "created_at" in r["measured"]


# ───────────────────────── Part 1c: seeded defects flip it (detectors, offline) ─────────────────────────

def _measure(spec=SPEC, rows=ROWS, chunks=CHUNKS, state=CAR["citation_state"]):
    return d1.d1_measure(spec, state, chunks, copy.deepcopy(rows), AID)


def test_the_committed_spec_passes_d1_on_the_real_rows_and_chunks_and_says_what_it_proves():
    r = _measure()
    assert r["v"] == PASS and r["citation_state"] == "sourced_ocr_unverified" and r["d1"]["rows_matched"] == 8 and r["d1"]["unmatched"] == []
    assert r["d1"]["translation_only"] is True and r["d1"]["content_sa_all_null"] is True
    assert all(c["verified"] and c["preimage"] == "text_id::content_en" for c in r["d1"]["chunks"])
    for needle in ("ENGLISH translation", "OCR text not checked against the printed book", "text_id-prefixed"):
        assert needle in r["measured"]


def test_a_wrong_chunk_id_is_no_detector_naming_it():
    spec = copy.deepcopy(SPEC)
    spec["chunk_ids"] = [IDS[0], "phaladeepika_pg0340_c01"]
    r = _measure(spec=spec)
    assert r["v"] == NO_DET and "phaladeepika_pg0340_c01" in r["measured"]


def test_a_clause_that_is_not_in_the_passage_is_a_miss_naming_the_row():
    spec = copy.deepcopy(SPEC)
    spec["effect_clauses"]["Venus"]["clause"] = "There will be great joy in the Latta of Venus"
    r = _measure(spec=spec)
    assert r["v"] == PARTIAL and [u["row"] for u in r["d1"]["unmatched"]] == ["Venus"]


def test_an_effect_that_does_not_match_the_clause_is_a_miss_in_either_place():
    spec = copy.deepcopy(SPEC)
    spec["effect_clauses"]["Moon"]["effect"] = "A great gain."
    r = _measure(spec=spec)
    assert r["v"] == PARTIAL and [u["row"] for u in r["d1"]["unmatched"]] == ["Moon"]
    rows = copy.deepcopy(ROWS)
    [x.update(effect_description="Quarrel.") for x in rows if x["graha"] == "Moon"]
    r = _measure(rows=rows)
    assert r["v"] == PARTIAL and [(u["row"], u["failed"]) for u in r["d1"]["unmatched"]] == [("Moon", ["effect"])]


def test_mars_and_saturn_stay_reserved_empty_and_a_ketu_row_cannot_be_sourced():
    rows = copy.deepcopy(ROWS)
    [x.update(effect_description="Misery.") for x in rows if x["graha"] == "Mars"]
    assert [u["row"] for u in _measure(rows=rows)["d1"]["unmatched"]] == ["Mars"]
    ketu = copy.deepcopy([x for x in ROWS if x["graha"] == "Rahu"][0])
    ketu["graha"] = "Ketu"          # Rahu's clause names Ketu, but the passage gives Ketu no counting rule
    r = _measure(rows=copy.deepcopy(ROWS) + [ketu])
    assert r["v"] == PARTIAL and [u["row"] for u in r["d1"]["unmatched"]] == ["Ketu"]


def test_vocab_column_drift_is_a_fail_and_a_declared_unsourced_state_is_no_detector_on_both_citation_checks():
    va = dict(VA, vocab_column="planet")
    assert ac.vocab_alias_declared_check(AID, va, AID, COLS)["Vocab.alias"]["v"] == FAIL
    assert _measure(state="unsourced")["v"] == NO_DET and _measure(state="refuted")["v"] == NO_DET
    ls = dict(LS, citation_state="unsourced")
    assert ac.grade_ldgr_source(ls, dict(rows=8, lacking=0), AID)["v"] == NO_DET
    rec = ac.grade_ldgr_source(LS, dict(rows=8, lacking=0), AID)
    assert rec["v"] == PASS and rec["citation_state"] == "sourced_ocr_unverified"


def test_a_stale_source_citation_page_is_recorded_not_matched_the_span_is_what_d1_matches():
    """Finding: source_citation names PG339 only on 8 of 8 rows. D1 matches the declared passage span (verse_ref), not each row's page string."""
    assert {r["source_citation"] for r in ROWS} == {PG339} and {r["verse_ref"] for r in ROWS} == {"Adh.XXVI PG338-339 Sloka 42-44"}
    assert _measure()["v"] == PASS
    assert not any("source_citation" in json.dumps(e) for e in SPEC["extra_fields"])


def test_the_two_corpus_sources_agree_where_both_exist():
    if not CORPUS_FILE.exists():
        pytest.skip("the corpus export is not on this machine (CI): the committed fixture was used")
    fx = s2.FX
    key = lambda rs: {r["graha"]: (r["count_from_graha"], r["direction"], r["effect_description"], r["affliction_condition"], r["verse_ref"]) for r in rs}
    assert key(fx["bg_phaladeepika_latta"]) == key(ROWS)
    assert {c["chunk_id"]: (c["content_en"], c["content_sha256"]) for c in fx["classical_text_chunks"]} == {k: (c["content_en"], c["content_sha256"]) for k, c in CHUNKS.items()}


# ───────────────────────── Part 2: REAL detectors on a disposable Postgres ─────────────────────────

def _lit(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def _setup():
    out = [f"CREATE TEMP TABLE {AID} (table_version text NOT NULL, graha text NOT NULL, count_from_graha smallint NOT NULL, direction text NOT NULL CHECK (direction IN ('forward','backward')), "
           "effect_description text, affliction_condition text NOT NULL, source_citation text NOT NULL, verse_ref text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), "
           "PRIMARY KEY (table_version, graha)) ON COMMIT DROP;"]
    out += [f"INSERT INTO {AID} (" + ",".join(COLS) + ") VALUES (" + ",".join(_lit(r[c]) for c in COLS) + ");" for r in ROWS]
    ck = ("chunk_id", "text_id", "content_en", "content_sa", "content_sha256")
    out.append("CREATE TEMP TABLE classical_text_chunks (chunk_id text, text_id text, content_en text, content_sa text, content_sha256 text) ON COMMIT DROP;")
    out += ["INSERT INTO classical_text_chunks VALUES (" + ",".join(_lit(c[k]) for k in ck) + ");" for c in CHUNK_LIST]
    out.append("CREATE TEMP TABLE brahma_ontology (entity_class text, canonical_id text, canonical_name_en text, synonyms text[]) ON COMMIT DROP;")
    out.append("INSERT INTO brahma_ontology VALUES " + ",".join(f"('planet','{i}','{i.title()}',ARRAY[]::text[])" for i in ONTOLOGY) + ";")
    return out


def _measure_all(monkeypatch, pg):
    s3._real(monkeypatch, pg, _setup())
    m = {}
    m.update(ac.carriage_declared_checks(AID, CAR, AID, False, column_types=ac.carriage_fetch_column_types(AID), prose_columns=[]))
    m.update(ac.vocab_alias_declared_check(AID, VA, AID, COLS))
    m.update(ac.ldgr_source_declared_check(AID, LS, AID, COLS, [["table_version", "graha"]]))
    return m


def test_REAL_carr_d1_passes_with_the_citation_state_and_d2_d3_are_not_applicable(monkeypatch, disposable_pg):
    m = _measure_all(monkeypatch, disposable_pg)
    r = m["Carr.D1"]
    assert r["v"] == PASS and r["citation_state"] == "sourced_ocr_unverified" and r["d1"]["rows_matched"] == 8 and r["d1"]["row_count_ok"] is True
    assert all(c["verified"] for c in r["d1"]["chunks"]) and [c["chunk_id"] for c in r["d1"]["chunks"]] == IDS
    assert m["Carr.D2"]["v"] == NA and m["Carr.D3"]["v"] == NA and m["Carr.D2"]["cause"] == "no-per-witness-values"            # N-156: the latta declares per_witness_values false
    cell = ac.rollup_asset("L0", {k: m[k] for k in ("Carr.D1", "Carr.D2", "Carr.D3")})["Carr"]
    d1c = next(c for c in cell["checks"] if c["criterion"] == "Carr.D1")
    assert cell["v"] == PASS and d1c["citation_state"] == "sourced_ocr_unverified"


def test_REAL_vocab_alias_passes_by_identity_only_on_all_eight_grahas_and_ketu_is_absent(monkeypatch, disposable_pg):
    r = _measure_all(monkeypatch, disposable_pg)["Vocab.alias"]
    assert r["v"] == PASS and r["alias"]["rows"] == 8 and r["alias"]["distinct_values"] == 8 and r["alias"]["unresolved"] == {}
    assert "identity_only declared" in r["measured"] and sorted(v for vs in r["alias"]["resolved_by"].values() for v in vs) == sorted(g["graha"] for g in ROWS)
    assert "Ketu" not in {g["graha"] for g in ROWS}


def test_REAL_ldgr_source_passes_on_verse_ref_and_carries_the_caveat(monkeypatch, disposable_pg):
    r = _measure_all(monkeypatch, disposable_pg)["Ldgr.source_presence"]
    assert r["v"] == PASS and r["citation_state"] == "sourced_ocr_unverified" and r["ldgr"]["source_column"] == "verse_ref"
    assert (r["ldgr"]["rows"], r["ldgr"]["lacking"]) == (8, 0)
    cell = ac.rollup_asset("L0", {"Ldgr.source_presence": r})["Ldgr"]
    chk = next(c for c in cell["checks"] if c["criterion"] == "Ldgr.source_presence")
    assert cell["v"] == PASS and chk["citation_state"] == "sourced_ocr_unverified"
    caveat = r["v"] == PASS and chk["citation_state"] != "sourced"                  # nikasha_certify: the caveat is "a PASS whose state is not `sourced`"
    assert caveat is True


def test_REAL_an_unsourced_state_makes_ldgr_no_detector_on_the_real_rows(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, _setup())
    r = ac.ldgr_source_declared_check(AID, dict(LS, citation_state="unsourced"), AID, COLS, [["table_version", "graha"]])["Ldgr.source_presence"]
    assert r["v"] == NO_DET and "unsourced" in r["measured"]


def test_REAL_a_blank_verse_ref_on_one_row_makes_ldgr_partial(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, _setup() + [f"UPDATE {AID} SET verse_ref = ' - ' WHERE graha = 'Sun';"])
    r = ac.ldgr_source_declared_check(AID, LS, AID, COLS, [["table_version", "graha"]])["Ldgr.source_presence"]
    assert r["v"] == PARTIAL and (r["ldgr"]["rows"], r["ldgr"]["lacking"]) == (8, 1)


def test_REAL_a_wrong_row_in_the_table_is_a_d1_partial_naming_it(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, _setup() + [f"UPDATE {AID} SET count_from_graha = 21 WHERE graha = 'Moon';"])
    r = ac.carriage_declared_checks(AID, CAR, AID, False, column_types=ac.carriage_fetch_column_types(AID), prose_columns=[])["Carr.D1"]
    assert r["v"] == PARTIAL and [u["row"] for u in r["d1"]["unmatched"]] == ["Moon"]


# ───────────────────────── Part 3: the cells this declaration changes, and the ones it does not ─────────────────────────

def test_the_narr_checks_are_untouched_by_this_declarations_three_blocks():
    """The three blocks measured here (carriage, vocab_alias, ldgr_source) do not touch Narr: with no prose_fields declared the four Narr checks read exactly NO_DETECTOR (undeclared).
    (Null is declared by 1.11.0: test_e6_decl_latta_null.py; prose_fields [] + prose_coupling arrive with 1.12.0, NARR-GUARD: test_e6_narr_guard.py, which measures them.)"""
    cat = dict(exists={AID}, cols={AID: COLS}, keys={AID: [["table_version", "graha"]]}, views=set(), types={AID: {c: "text" for c in COLS}},
               defaults={AID: {}}, types_error=None)
    undeclared = dict(ENTRY, null_convention=None, prose_fields=None, prose_coupling=None, evidence_kind=None, evidence=dict(ENTRY["evidence"], prose_fields=None))
    m = ac._measure_prose(AID, undeclared, dict(target_table=AID, count_sql=f"SELECT count(*) FROM {AID}"), None, cat, [], set(), (), set())
    assert {c: m[c]["v"] for c in ac.NARR_CHECKS} == {c: NO_DET for c in ac.NARR_CHECKS}
    assert all("prose_fields is undeclared" in m[c]["measured"] for c in ac.NARR_CHECKS)


@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_REAL_cells_before_and_after_on_the_saved_census(monkeypatch, disposable_pg):
    saved = [a for a in json.loads((SAVED / "census_L0.json").read_text(encoding="utf-8"))["L0"]["assets"] if a["asset_id"] == AID][0]
    before = ac.rollup_asset("L0", saved["measurements"])
    m = _measure_all(monkeypatch, disposable_pg)
    meas = {k: v for k, v in saved["measurements"].items() if k not in ("Ldgr.source_presence", "Vocab.alias")}
    meas.update(m)
    after = ac.rollup_asset("L0", meas)
    b, a = {g: c["v"] for g, c in before.items()}, {g: c["v"] for g, c in after.items()}
    assert (b["Carr"], a["Carr"]) == (NO_DET, PASS) and (b["Vocab"], a["Vocab"]) == (NO_DET, PASS) and (b["Ldgr"], a["Ldgr"]) == (PASS, PASS)
    for g in ("Null", "Narr", "Earn", "Dens"):                      # unchanged BY THESE THREE BLOCKS (this test measures no Null record; Null is 1.11.0's: test_e6_decl_latta_null.py)
        assert b[g] == a[g] == NO_DET, g
    for g in ("Idem", "Build"):
        assert b[g] == a[g] == PASS, g
    moved = sorted(g for g in b if b[g] != a[g])
    assert moved == ["Carr", "Vocab"]                                # Ldgr stays PASS (its basis moves from source_citation to verse_ref + citation_state)
    assert next(c for c in after["Ldgr"]["checks"] if c["criterion"] == "Ldgr.source_presence")["citation_state"] == "sourced_ocr_unverified"
    assert "citation_state" not in next(c for c in before["Ldgr"]["checks"] if c["criterion"] == "Ldgr.source_presence")


# ───────────────────────── evidence pointers land on the line that supports them ─────────────────────────

ROOT = ac.ROOT
FIXT = "platform/scripts/governance/__tests__/fixtures/phaladeepika_latta_d1_fixture.json"


def _line(ptr):
    rel, n = ptr.rsplit(":", 1)
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()[int(n) - 1]


def test_every_evidence_pointer_lands_on_the_line_that_supports_its_claim():
    """The validator accepts ANY in-range line: pin the target line content so a drifted or wrong line fails."""
    assert CAR["evidence"] == "platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:122" and "LATTA_ROWS" in _line(CAR["evidence"])
    assert "verbatim" not in _line(CAR["evidence"]).lower()                      # not the refuted '# ... verbatim from' comment two lines above
    assert VA["evidence"] == "platform/supabase/migrations/528_bg_phaladeepika_vedha.sql:106" and re.match(r"\s*graha\s+TEXT", _line(VA["evidence"]))
    assert LS["evidence"] == "platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:84" and "_VERSE_REF_LATTA" in _line(LS["evidence"])
    ptrs = [SPEC["effect_clauses_evidence"]]
    for ef in SPEC["extra_fields"]:
        if ef["kind"] == "passage_text":
            c = ef["condition"]
            ptrs += [ef["condition_evidence"], c["ocr_lost_stop"]["evidence"]] + [h["evidence"] for h in c["ocr_stops"]] + [r["evidence"] for r in ef["repairs"]]
    assert ptrs and set(ptrs) == {f"{FIXT}:27"}
    assert '"content_en": "Adh. XXVI' in _line(ptrs[0])                            # the PG339 chunk text the clauses and the OCR garbles are read from
