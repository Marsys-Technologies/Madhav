"""TI-L0-13 (SS Q4, CF-09 (c)): the ontology `text` class is derived from the corpus manifest.

Live pre-state: ontology 15 text ids, corpus 15, differing by 3 in each direction. Proves
  1. the text class = corpus manifest ids + the one ontology-only id with a consumer
     (jaimini_sutram); the 3 corpus-only ids are added; bhrigu_samhita and lal_kitab_text
     (no consumer, not corpus texts) are no longer emitted; the derivation is a pure function
     of the manifest (a text added to the manifest appears).
  2. the 12 texts that existed in both places keep name / synonyms / description / citation
     VERBATIM (golden, written from the production rows read 2026-10-03).
  3. a static referrer census: the two removed ids are named by no source file outside the
     allow-listed comments/docs, and jaimini_sutram's consumers are exactly the ones named (l0_yogas.py x12, l0_dasha_systems.py x5, migration 465 x7).
  4. beneficiaries: every text_id held by sutravali_rules (14 ids), brahma_compendium_index (15)
     and the corpus resolves; remedy source ids: exact 54 / case-only 204 / unresolved 83
     (80 'classical_tradition' = not provenance, SS Q3; 3 'Tajaka' = the school, not a text).
  5. real PostgreSQL (env-gated): the REAL seed_ontology over the production-shaped pre-state
     adds exactly 3 rows, removes exactly 2, changes nothing else (12 legacy rows byte-equal incl.
     their uuid), leaves co-writer rows alone, and a rerun is a no-op.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from brahmagyan import l0_ontology as O
from brahmagyan import l0_ontology_texts as TXO
from brahmagyan import l0_texts as TX
from tests._l0d_pg import requires_pg, scratch_schema

FIX = json.loads((Path(__file__).parent / "fixtures" / "l0_ontology_remedy_source_ids.json").read_text(encoding="utf-8"))["counts"]

CORPUS_IDS = {t["text_id"] for t in TX.TEXTS}
NEW_IDS = {"bhrigu_nandi_nadi", "bphs_jaimini", "nadi_navamsa_patel"}
REMOVED_IDS = {"bhrigu_samhita", "lal_kitab_text"}
KEPT_ONTOLOGY_ONLY = {"jaimini_sutram"}

# production rows read 2026-10-03: (name_en, name_sa, synonyms, description)
LEGACY = {
    "bphs": ("Brihat Parashara Hora Shastra", "Bṛhat Parāśara Horā Śāstra", ["bphs", "brihat parasara", "parashara hora"], "Foundational Parashari text"),
    "phaladeepika": ("Phaladeepika", "Phaladīpikā", ["phaladeepika"], "Mantreswara's predictive synthesis"),
    "jataka_parijata": ("Jataka Parijata", "Jātaka Pārijāta", ["jataka parijata", "parijata"], "Vaidyanatha Dikshita's comprehensive natal text"),
    "uttara_kalamrita": ("Uttara Kalamrita", "Uttara Kālāmṛta", ["uttara kalamrita", "kalamrita"], "Kalidasa's compact reference"),
    "brihat_jataka": ("Brihat Jataka", "Bṛhat Jātaka", ["brihat jataka", "varahamihira jataka"], "Varahamihira's natal classic"),
    "saravali": ("Saravali", "Sārāvalī", ["saravali", "kalyana varma"], "Kalyana Varma's extensive yoga catalog"),
    "hora_sara": ("Hora Sara", "Horā Sāra", ["hora sara", "prithuyasas"], "Prithuyasas's predictive text"),
    "sarvartha_chintamani": ("Sarvartha Chintamani", "Sarvārtha Cintāmaṇi", ["sarvartha chintamani", "chintamani"], "Venkatesha's predictive compendium"),
    "brihat_samhita": ("Brihat Samhita", "Bṛhat Saṃhitā", ["brihat samhita", "samhita"], "Varahamihira's mundane/omens encyclopedia"),
    "tajaka_neelakanthi": ("Tajaka Neelakanthi", "Tājaka Nīlakaṇṭhī", ["tajaka neelakanthi", "neelakanthi"], "Neelakantha's annual-chart text"),
    "yavana_jataka": ("Yavana Jataka", "Yavana Jātaka", ["yavana jataka"], "Sphujidhvaja's Greek-influenced natal text"),
    "muhurta_chintamani": ("Muhurta Chintamani", "Muhūrta Cintāmaṇi", ["muhurta chintamani"], "Rama's electional-astrology text"),
}
REMOVED_ROWS = {   # production rows, to build the pre-state
    "bhrigu_samhita": ("Bhrigu Samhita", "Bhṛgu Saṃhitā", ["bhrigu samhita", "bhrigu"], "Bhrigu's predictive compendium (extracts)"),
    "lal_kitab_text": ("Lal Kitab", "Lāl Kitāb", ["lal kitab text"], "The Lal Kitab remedial corpus"),
}
BPHS = "BPHS (Brihat Parasara Hora Sastra), classical tradition"

# text_ids held by the beneficiary tables (read-only production census 2026-10-03)
SUTRAVALI_RULES_TEXT_IDS = ["bhrigu_nandi_nadi", "bphs", "bphs_jaimini", "brihat_jataka", "brihat_samhita", "hora_sara", "jataka_parijata",
                            "muhurta_chintamani", "nadi_navamsa_patel", "phaladeepika", "saravali", "sarvartha_chintamani",
                            "uttara_kalamrita", "yavana_jataka"]


def text_rows():
    return {e["canonical_id"]: e for e in O.ENTITIES if e["entity_class"] == "text"}


# ── 1 ────────────────────────────────────────────────────────────────────────

def test_manifest_is_the_15_corpus_texts():
    assert len(CORPUS_IDS) == 15 and NEW_IDS <= CORPUS_IDS


def test_text_class_is_corpus_plus_the_one_ontology_only_id_with_a_consumer():
    assert set(text_rows()) == CORPUS_IDS | KEPT_ONTOLOGY_ONLY
    assert len(text_rows()) == 16
    assert not (set(text_rows()) & REMOVED_IDS)


def test_derivation_is_a_pure_function_of_the_manifest():
    fake = {"text_id": "zz_new_text", "title_en": "A New Text", "title_sa": None, "author": "Someone",
            "school": "parashari", "source_citation": "A New Text - Some Edition"}
    out = {e["canonical_id"]: e for e in TXO.derive_missing_text_entities(O.ENTITIES, list(TX.TEXTS) + [fake])}
    assert set(out) == {"zz_new_text"}, "only the manifest text the class lacks is derived"
    assert out["zz_new_text"]["source_citation"] == "A New Text - Some Edition"
    assert out["zz_new_text"]["synonyms"] == ["a new text", "zz new text"]
    # an empty class derives the whole manifest
    assert {e["canonical_id"] for e in TXO.derive_missing_text_entities([], TX.TEXTS)} == CORPUS_IDS


def test_the_class_cannot_drift_from_the_manifest_again():
    TXO.assert_text_class_matches_manifest(O.ENTITIES)                      # holds today (also run at import)
    fake = {"text_id": "zz_new_text", "title_en": "A", "title_sa": None, "author": "x", "school": "y", "source_citation": "z"}
    with pytest.raises(ValueError, match="zz_new_text"):
        TXO.assert_text_class_matches_manifest(O.ENTITIES, list(TX.TEXTS) + [fake])           # corpus-only id
    with pytest.raises(ValueError, match="saravali"):
        TXO.assert_text_class_matches_manifest(O.ENTITIES, [t for t in TX.TEXTS if t["text_id"] != "saravali"])  # ontology-only id, no consumer declared
    assert TXO.TEXT_ONTOLOGY_ONLY_KEPT == {"jaimini_sutram"}


@pytest.mark.parametrize("cid", sorted(NEW_IDS))
def test_new_rows_take_every_field_from_the_manifest_and_are_sourced_not_the_bphs_placeholder(cid):
    row = text_rows()[cid]
    m = next(t for t in TX.TEXTS if t["text_id"] == cid)
    assert row["canonical_name_en"] == m["title_en"] and row["canonical_name_sa"] == m.get("title_sa")
    assert row["source_citation"] == m["source_citation"] != BPHS
    assert row["description"] == f'{m["author"]}; {m["school"]} school'
    assert row["synonyms"] and all(s == s.lower() for s in row["synonyms"])


# ── 2 ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("cid", sorted(LEGACY))
def test_the_12_legacy_texts_are_byte_for_byte_unchanged(cid):
    row = text_rows()[cid]
    name_en, name_sa, syn, desc = LEGACY[cid]
    assert (row["canonical_name_en"], row["canonical_name_sa"], row["synonyms"], row["description"], row["source_citation"]) \
        == (name_en, name_sa, syn, desc, BPHS)


def test_jaimini_sutram_is_kept_verbatim():
    row = text_rows()["jaimini_sutram"]
    assert (row["canonical_name_en"], row["canonical_name_sa"], row["synonyms"], row["description"]) == (
        "Jaimini Sutram", "Jaimini Sūtram", ["jaimini sutram", "jaimini sutras"], "The Jaimini aphorisms")


# ── 3 referrer census (static) ───────────────────────────────────────────────

REPO = Path(__file__).resolve().parents[3]
ALLOW_REMOVED = {  # files that may MENTION a removed id (prose, not a consumer)
    "platform/python-sidecar/brahmagyan/l0_texts.py",       # docstring: 'Dropped: lal_kitab, bhrigu_samhita'
    "platform/python-sidecar/brahmagyan/l0_ontology.py",    # the comment explaining the removal
    "platform/python-sidecar/brahmagyan/l0_ontology_texts.py",    # the docstring explaining the removal
    "platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_bg_texts.py",
    "platform/python-sidecar/brahmagyan/l0_rechunk_phase2.py",
    "platform/python-sidecar/brahmagyan/l0_run_phase2.py",
    "platform/python-sidecar/brahmagyan/l0_text_ingest_phase2.py",
    "platform/supabase/migrations/190_bg_text_index_floor.sql",
    "platform/supabase/migrations/_archive/154_g29_timing_rules.sql",
    "platform/src/lib/contract/registry.ts",
    "platform/scripts/audit/tap/tap6_method_grep.ts",
}


def _source_files():
    for root in ("platform/python-sidecar", "platform/src", "platform-mcp/src", "platform/scripts", "platform/supabase/migrations"):
        base = REPO / root
        for p in base.rglob("*"):
            if p.suffix in {".py", ".ts", ".tsx", ".sql", ".yaml", ".json"} and "node_modules" not in p.parts \
                    and "/tests/" not in str(p) and "__tests__" not in p.parts and "test_" not in p.name \
                    and "generated" not in p.parts and "fixtures" not in p.parts:
                yield p


def test_removed_ids_have_no_consumer_in_source():
    pat = re.compile(r"\b(bhrigu_samhita|lal_kitab_text)\b")
    hits = sorted({str(p.relative_to(REPO)) for p in _source_files() if pat.search(p.read_text(encoding="utf-8", errors="ignore"))})
    unexpected = [h for h in hits if h not in ALLOW_REMOVED]
    assert unexpected == [], f"source files name a removed text id: {unexpected}"


def test_jaimini_sutram_consumers_are_the_named_catalogue_citations():
    pat = re.compile(r"""["']text_id["']\s*:\s*["']jaimini_sutram["']""")
    counts = {}
    for p in _source_files():
        n = len(pat.findall(p.read_text(encoding="utf-8", errors="ignore")))
        if n:
            counts[str(p.relative_to(REPO))] = n
    assert counts == {"platform/python-sidecar/brahmagyan/l0_yogas.py": 12,
                      "platform/python-sidecar/brahmagyan/l0_dasha_systems.py": 5,
                      "platform/supabase/migrations/465_cr130_jaimini_karakamsha_yogas.sql": 7}, counts


# ── 4 beneficiaries ──────────────────────────────────────────────────────────

def test_every_beneficiary_text_id_resolves_exactly():
    ids = set(text_rows())
    assert set(SUTRAVALI_RULES_TEXT_IDS) <= ids
    assert CORPUS_IDS <= ids


def test_remedy_source_ids_exact_54_case_only_204_unresolved_83():
    ids = set(text_rows())
    lower = {i.lower() for i in ids}
    tally = {"exact": 0, "case_only": 0, "unresolved": 0}
    for sid, n in FIX.items():
        tally["exact" if sid in ids else "case_only" if sid.lower() in lower else "unresolved"] += n
    assert tally == {"exact": 54, "case_only": 204, "unresolved": 83}, tally


# ── 5 real PostgreSQL ────────────────────────────────────────────────────────

DDL = """
CREATE TABLE brahma_ontology (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(), entity_class text NOT NULL, canonical_id text NOT NULL,
  canonical_name_en text NOT NULL, canonical_name_sa text, synonyms text[] NOT NULL DEFAULT '{}',
  description text, source_citation text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT brahma_ontology_canonical_unique UNIQUE (entity_class, canonical_id));
"""
COLS = "id,entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation"


@requires_pg
def test_real_writer_adds_3_removes_2_and_changes_nothing_else():
    with scratch_schema(DDL) as conn:
        O.seed_ontology(conn, autocommit=False)
        # production-shaped pre-state: 15 text rows (12 legacy + jaimini_sutram + the 2 removed), none of the 3 new
        conn.execute("DELETE FROM brahma_ontology WHERE entity_class='text' AND canonical_id = ANY(%s)", (sorted(NEW_IDS),))
        for cid, (en, sa, syn, desc) in REMOVED_ROWS.items():
            conn.execute("INSERT INTO brahma_ontology(entity_class,canonical_id,canonical_name_en,canonical_name_sa,synonyms,description,source_citation) "
                         "VALUES ('text',%s,%s,%s,%s,%s,%s)", (cid, en, sa, syn, desc, BPHS))
        # co-writer rows owned by siblings must survive untouched
        conn.execute("INSERT INTO brahma_ontology(entity_class,canonical_id,canonical_name_en,synonyms,source_citation) "
                     "VALUES ('yoga','zz_yoga','Z','{z}','y'),('dosha','zz_dosha','Z','{}','y'),('dasha_system','zz_ds','Z','{z}','y')")
        conn.commit()
        before = {r["canonical_id"]: r for r in conn.execute(f"SELECT {COLS} FROM brahma_ontology WHERE entity_class='text'")}
        others = list(conn.execute(f"SELECT {COLS} FROM brahma_ontology WHERE entity_class<>'text' ORDER BY entity_class,canonical_id"))
        assert len(before) == 15 and set(before) & REMOVED_IDS == REMOVED_IDS and not (set(before) & NEW_IDS)

        O.seed_ontology(conn, autocommit=False)
        conn.commit()
        after = {r["canonical_id"]: r for r in conn.execute(f"SELECT {COLS} FROM brahma_ontology WHERE entity_class='text'")}
        assert set(after) == CORPUS_IDS | KEPT_ONTOLOGY_ONLY and len(after) == 16
        assert set(after) - set(before) == NEW_IDS and set(before) - set(after) == REMOVED_IDS
        for cid in set(before) & set(after):
            assert before[cid] == after[cid], f"{cid} changed (incl. its uuid)"
        assert list(conn.execute(f"SELECT {COLS} FROM brahma_ontology WHERE entity_class<>'text' ORDER BY entity_class,canonical_id")) == others
        snap = list(conn.execute(f"SELECT {COLS} FROM brahma_ontology ORDER BY entity_class,canonical_id"))
        out = O.seed_ontology(conn, autocommit=False)
        conn.commit()
        assert out["inserted"] == 0 and list(conn.execute(f"SELECT {COLS} FROM brahma_ontology ORDER BY entity_class,canonical_id")) == snap


# ── SS N-113 (d): the stray co-writer row dasha_system|jaimini_chara ──────────────────────────────────────────
# A bg_ontology rebuild used to INSERT `dasha_system|jaimini_chara` (the static ENTITIES list carried it; the dasha
# catalogue's id is `chara_jaimini`): 741 -> 742 rows, and the bg_dasha_systems sealed check (20 ontology dasha rows)
# went false until bg_dasha_systems was rebuilt. The row is removed from ENTITIES.

def _catalogue_dasha_ids() -> set[str]:
    from brahmagyan import l0_dasha_systems as DS
    return {d["canonical_id"] for d in DS.DASHA_SYSTEMS}


def test_every_co_writer_entity_in_the_static_list_is_a_catalogue_id_so_a_rebuild_can_never_insert_a_stray():
    ids = _catalogue_dasha_ids()
    assert len(ids) == 20
    for e in O.ENTITIES:
        if e["entity_class"] == "dasha_system":
            assert e["canonical_id"] in ids, f"stray co-writer entity {e['canonical_id']!r}: not in the dasha catalogue"
    assert not any(e["canonical_id"] == "jaimini_chara" for e in O.ENTITIES)


@requires_pg
def test_real_bg_ontology_rebuild_keeps_the_row_count_and_the_dasha_class_at_20():
    from brahmagyan import l0_dasha_systems as DS
    with scratch_schema(DDL) as conn:
        # production-shaped: the whole ontology as bg_ontology + the co-writers leave it, dasha class = the 20 catalogue ids
        O.seed_ontology(conn, autocommit=False)
        conn.execute("DELETE FROM brahma_ontology WHERE entity_class='dasha_system'")
        for d in DS.DASHA_SYSTEMS:
            conn.execute("INSERT INTO brahma_ontology(entity_class,canonical_id,canonical_name_en,synonyms,source_citation) "
                         "VALUES ('dasha_system',%s,%s,'{}','x')", (d["canonical_id"], d["canonical_id"]))
        conn.commit()
        before = conn.execute("SELECT count(*) AS n FROM brahma_ontology").fetchone()["n"]
        dasha_before = conn.execute("SELECT count(*) AS n FROM brahma_ontology WHERE entity_class='dasha_system'").fetchone()["n"]
        assert dasha_before == 20
        for _ in range(2):            # first run and a converged rerun
            out = O.seed_ontology(conn, autocommit=False)
            conn.commit()
            assert conn.execute("SELECT count(*) AS n FROM brahma_ontology").fetchone()["n"] == before, "rebuild must KEEP the row count"
            assert conn.execute("SELECT count(*) AS n FROM brahma_ontology WHERE entity_class='dasha_system'").fetchone()["n"] == 20
        assert out["deleted"] == 0 and out["inserted"] == 0
