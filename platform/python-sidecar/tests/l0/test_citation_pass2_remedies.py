"""CITATION-PASS2 (decision OS-2026-10-05-CITATIONS) — bg_remedies (brahma_remedy_corpus) seed overlay, tested by natural key (remedy_id).

Implements the 101 brahma_remedy_corpus rows of ACHARYA/CITATION_PASS2/PASS2_DECISIONS.tsv: 25 REMOVE, 30 CONTENT_FIX+K1, 5 CONTENT_FIX+K2, 40 LABEL_K2_MODERN,
1 KEEP_UNVERIFIED_LABELLED. Pure offline: the seed builder only, no database. The census's Ldgr citation-placeholder rule is read by the shared
Python mirror (tests/_citation_pass2_ldgr.py).
"""
from __future__ import annotations

import re
from collections import Counter

import pytest

from brahmagyan import citation_pass2_remedies as C
from brahmagyan import l0_remedy_corpus as L
from tests._citation_pass2_ldgr import citation_lacks_source

K2_ID = "OS-2026-10-05-CITATIONS"
K2_SRC = "k2:OS-2026-10-05-CITATIONS"

REMOVED = {
    "dosha_bhakoot_vishnu_puja", "dosha_graha_maitri_puja", "dosha_mahendra_vishnu_puja", "dosha_gana_shiva_puja", "dosha_rajju_shiva_puja",
    "dosha_stree_deergha_puja", "dosha_tara_nakshatra_puja", "dosha_vedha_nakshatra_puja", "dosha_varna_surya_mantra", "dosha_vashya_venus_mantra",
    "dosha_yoni_puja", "dosha_vish_dosha_shani_chandra", "dosha_vish_kanya_puja",
    *{f"dosha_kala_sarpa_{v}_shanti" for v in (
        "anant", "ghatak", "karkotak", "kulik", "mahapadma", "padma", "shankhachud", "shankhpal", "sheshnag", "takshak", "vasuki", "vishdhar")},
}
K1_CONTENT = {f"{p}_matrix_{t}" for p in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu") for t in ("japa", "homa", "puja")} | {
    "dosha_abhukta_mula_shanti", "dosha_mool_shanti", "dosha_nadi_mahamrityunjaya"}
K2_CONTENT = {"stotra_saraswati_mercury_education", "yantra_kala_sarpa_shanti", "dosha_punarphoo_shani_mantra", "dosha_sade_sati_shani_charity", "dosha_shrapit_shani_rahu"}
K2_LABEL = {f"{p}_matrix_{t}" for p in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu") for t in ("vrata", "yantra", "behavioral")} | {
    "dosha_guru_chandal_jupiter_puja", "dosha_shakata_guru_puja", "dosha_kala_amrita_shanti", "dosha_angarak_mars_rahu", "dosha_kemadruma_compat_kuja_mars",
    "dosha_kuja_from_moon_hanuman", "dosha_kala_sarpa_mantra", "dosha_kala_sarpa_nag_puja", "dosha_dhaiya_shani_puja", "dosha_sade_sati_shani_mantra",
    "dosha_grahan_surya_chandra_mantra", "dosha_mrityu_bhaga_mantra", "dosha_pitru_surya_mantra"}
UNVERIFIED = {"dosha_pitru_tarpan"}
RENAMES = {"dosha_kemadruma_compat_kuja_mars": "dosha_kuja_from_venus_mars"}


def _pre_overlay_rows():
    """The seed rows exactly as they were before the overlay (build_all_remedies with apply_pass2 replaced by the identity)."""
    real = L.apply_pass2
    L.apply_pass2 = lambda rows: rows
    try:
        return {r["remedy_id"]: dict(r) for r in L.build_all_remedies()}
    finally:
        L.apply_pass2 = real


@pytest.fixture(scope="module")
def before():
    return _pre_overlay_rows()


@pytest.fixture(scope="module")
def after():
    return {r["remedy_id"]: r for r in L.build_all_remedies()}


# ---- decision-set bookkeeping --------------------------------------------------------------------------------------

def test_decision_sets_cover_exactly_the_101_tsv_remedy_rows():
    groups = [REMOVED, K1_CONTENT, K2_CONTENT, K2_LABEL, UNVERIFIED]
    assert [len(g) for g in groups] == [25, 30, 5, 40, 1]
    assert sum(len(g) for g in groups) == 101
    assert len(set().union(*groups)) == 101                      # no key in two groups
    assert C.REMOVED_REMEDY_IDS == REMOVED
    assert set(C.PASS2_EDITS) == K1_CONTENT | K2_CONTENT | K2_LABEL | UNVERIFIED   # 76 edited rows
    assert C.RENAMED_REMEDY_IDS == RENAMES


def test_row_counts_341_to_316_static_283_to_258(before, after):
    assert len(before) == 283 and len(after) == 258
    assert 283 - len(REMOVED) == 258
    assert 258 + 54 + 4 == 316                                    # + corpus-sweep rows + accepted tantric rows (the 608 contract's decomposition)


# ---- rows added / removed / changed by natural key -----------------------------------------------------------------

def test_removed_rows_are_absent_and_nothing_else_disappears(before, after):
    assert not (REMOVED & set(after))
    gone = set(before) - set(after)
    assert gone == REMOVED | set(RENAMES)                         # the rename is the only other id that leaves
    added = set(after) - set(before)
    assert added == set(RENAMES.values())


def test_rename_follows_the_dosha_rename(before, after):
    old, new = "dosha_kemadruma_compat_kuja_mars", "dosha_kuja_from_venus_mars"
    assert old not in after and new in after
    assert after[new]["dosha_target"] == "kuja_dosha_from_venus"
    assert after[new]["prescription_text"] == before[old]["prescription_text"]   # id and citation change; the content is the TSV's "RENAME remedy_id" only
    assert after[new]["source_canonical_id"] == K2_SRC


def test_untouched_rows_are_byte_identical(before, after):
    touched = REMOVED | set(C.PASS2_EDITS) | set(RENAMES.values())
    for rid, row in after.items():
        if rid in touched:
            continue
        assert row == before[rid], rid
    assert len(set(after) - touched) == 258 - 76


def test_edited_rows_change_only_the_fields_the_decision_names(before, after):
    allowed = {"source_citation", "source_canonical_id", "classical_ref", "classical_attestation_text", "prescription_text", "deity", "domain",
               "contraindications", "confidence"}
    for rid, edit in C.PASS2_EDITS.items():
        new = after[RENAMES.get(rid, rid)]
        old = before[rid]
        changed = {f for f in set(new) | set(old) if new.get(f) != old.get(f) and not (f == "remedy_id")}
        assert changed <= allowed | {"dosha_target"}, (rid, changed - allowed)
        assert new["source_citation"] == edit["source_citation"]
        assert new["source_citation"] != old["source_citation"]


# ---- K1 / K2 columns satisfy the Ldgr detector rules (offline) -----------------------------------------------------

@pytest.mark.parametrize("rid", sorted(C.PASS2_EDITS))
def test_citation_columns_name_a_source_not_a_placeholder(rid, after):
    row = after[RENAMES.get(rid, rid)]
    assert not citation_lacks_source(row["source_citation"]), rid
    assert not citation_lacks_source(row["source_canonical_id"]), rid
    assert row["source_canonical_id"] not in ("classical_tradition", "BPHS"), rid     # the two false attributions this pass replaces
    assert "classical tradition (Jyotish)" not in row["source_citation"]
    assert row.get("classical_ref") and row["classical_ref"].strip()                  # migration 608's not-blank conjunct (and 1323's) keeps holding


def _segments(cit: str) -> list[str]:
    return cit.split(" ; ")


K1_SEG = re.compile(r"^K1 — .+ — (?P<text>[a-z_]+):PG\d+:C\d+")


@pytest.mark.parametrize("rid", sorted(K1_CONTENT))
def test_k1_rows_carry_machine_and_human_locus_and_the_text_id_resolves(rid, after):
    row = after[rid]
    segs = [s for s in _segments(row["source_citation"]) if s.startswith("K1 — ")]
    assert segs, rid
    for s in segs:
        m = K1_SEG.match(s)
        assert m, (rid, s[:80])                                   # '<Text> <chapter/verse> — <text_id>:PGnnn:Cn'
        assert m["text"] == row["source_canonical_id"], (rid, m["text"])   # remedy source_canonical_id = the corpus text_id (record section 5)
    assert row["source_canonical_id"] in ("bphs", "muhurta_chintamani")
    assert "bphs:PG" in row["classical_ref"] or "muhurta_chintamani:PG" in row["classical_ref"]
    assert row["classical_attestation_text"].strip()


@pytest.mark.parametrize("rid", sorted(K2_LABEL | K2_CONTENT | UNVERIFIED))
def test_k2_rows_cite_the_decision_and_cap_confidence(rid, after, before):
    row = after[RENAMES.get(rid, rid)]
    assert K2_ID in row["source_citation"]
    assert row["source_canonical_id"] == (K2_SRC if rid not in UNVERIFIED else "k1_unverified")
    assert float(row["confidence"]) <= 0.60
    assert float(row["confidence"]) <= float(before[rid]["confidence"])          # a cap never raises


def test_every_k2_row_classical_ref_is_the_k2_label_never_classical(after):
    """SS ruling 3 (N-151): a K2 row is never dressed as classical. 42 rows take the K2 label wording; the three rows the TSV words individually keep theirs."""
    individually_worded = {"stotra_saraswati_mercury_education", "yantra_kala_sarpa_shanti", "dosha_sade_sati_shani_charity"}
    k2 = [r for r in after.values() if r["source_canonical_id"] == K2_SRC]
    assert len(k2) == 45
    for r in k2:
        if r["remedy_id"] in {RENAMES.get(i, i) for i in individually_worded}:
            continue
        assert r["classical_ref"] == "modern practice / project judgment — OS-2026-10-05-CITATIONS", r["remedy_id"]
    for r in k2:
        assert not r["classical_ref"].lower().startswith("classical tradition"), r["remedy_id"]
        assert not re.match(r"^BPHS Ch\.88", r["classical_ref"]), r["remedy_id"]


def test_k2_label_text_is_the_ratified_wording(after):
    for rid in K2_LABEL | K2_CONTENT:
        assert after[RENAMES.get(rid, rid)]["source_citation"].startswith(
            "K2 — modern practice / project judgment, not a classical source; ratified OS-2026-10-05-CITATIONS"), rid


def test_unverified_row_is_labelled_not_verified(after):
    row = after["dosha_pitru_tarpan"]
    assert row["source_citation"].startswith("K1_UNVERIFIED — ")
    assert "not verified in our library" in row["source_citation"]
    assert row["source_canonical_id"] == "k1_unverified"
    assert row["classical_ref"] == "dharmaśāstra śrāddha prescription — text not in library"


def test_k2_decision_id_has_the_register_shape():
    assert re.fullmatch(r"OS-\d{4}-\d{2}-\d{2}-[A-Z]+", K2_ID)


# ---- content corrections --------------------------------------------------------------------------------------------

def test_homa_rows_drop_the_1008_standard_and_name_the_samidha(after):
    wood = {"sun": "arka (Aak)", "moon": "palāśa", "mars": "khadira (Khair)", "mercury": "apāmārga (Chirchiri)", "jupiter": "pippala (aśvattha)",
            "venus": "udumbara (Goolar)", "saturn": "śamī", "rahu": "dūrvā (Doob)", "ketu": "kuśa"}
    for p, w in wood.items():
        t = after[f"{p}_matrix_homa"]["prescription_text"]
        assert "1008 ahutis is the standard" not in t and f"samidhā {w}" in t and "108 (or 28) āhutis" in t, p


def test_japa_rows_carry_the_bphs_count_and_mars_keeps_10000_flagged_with_the_literal_scan(after, before):
    counts = {"sun": "7,000", "moon": "11,000", "mercury": "9,000", "jupiter": "19,000", "venus": "16,000", "saturn": "23,000", "rahu": "18,000", "ketu": "17,000"}
    for p, n in counts.items():
        assert f"count of {n}" in after[f"{p}_matrix_japa"]["prescription_text"], p
    mars = after["mars_matrix_japa"]["prescription_text"]
    assert "count of 10,000" in mars                                                       # SS ruling 1: the stored count STAYS 10,000
    assert 'count under verification: corpus scan reads "I 1000" (10,000 or 11,000); row keeps 10,000 until the page image is checked' in mars
    assert "Mars 10,000" in before["mars_matrix_japa"]["prescription_text"]
    assert "Sun 7,000; Moon 11,000" not in after["sun_matrix_japa"]["prescription_text"]   # the verbatim nine-planet list is dropped
    for p in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"):
        row = after[f"{p}_matrix_japa"]
        for col in (row["source_citation"], row["classical_attestation_text"]):
            assert "Mars I 1000" in col                                                    # the K1 excerpt quotes the scan LITERALLY ...
            assert "Mars 11000" not in col and "OCR reads" not in col                      # ... and never normalises it to 11000


def test_puja_rows_are_the_bphs_template_with_the_modern_deity_moved_to_the_note(after):
    for p in ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"):
        row = after[f"{p}_matrix_puja"]
        assert row["prescription_text"].startswith(f"Graha-śānti pūjā of {p.capitalize()} per BPHS Ch.84 §15-16")
        assert row["deity"] == f"{p.capitalize()} (BPHS Ch.84 §6-13 dhyāna form)"
        assert "Aṣṭottara-śata-nāma" in row["prescription_text"]


def test_mool_abhukta_nadi_corrections(after):
    mool = after["dosha_mool_shanti"]["prescription_text"]
    assert "27th day" not in mool and "classical prescriptive timing in tradition" not in mool and "Ch.94" in mool
    abh = after["dosha_abhukta_mula_shanti"]
    assert "immediately after birth" not in abh["prescription_text"] and "12th day" in abh["prescription_text"]
    assert abh["deity"] == "Rākṣasa (Mūla); adhideva Indra; pratyadhideva Jala"
    nadi = after["dosha_nadi_mahamrityunjaya"]
    assert nadi["source_canonical_id"] == "muhurta_chintamani" and "golden nāḍī" in nadi["prescription_text"]


def test_k2_content_corrections(after):
    assert "1,08,000" not in after["dosha_shrapit_shani_rahu"]["prescription_text"]
    assert "Śani and Rāhu mantras (count a project parameter)" in after["dosha_shrapit_shani_rahu"]["prescription_text"]
    assert "modern pilgrimage practice" in after["dosha_shrapit_shani_rahu"]["prescription_text"]
    y = after["yantra_kala_sarpa_shanti"]
    assert "Source: classical tradition" not in y["prescription_text"] and "Customarily installed" in y["prescription_text"]
    assert y["classical_ref"] == "modern Kala Sarpa Shanti yantra practice"
    assert "Deva Keralam" not in after["stotra_saraswati_mercury_education"]["classical_ref"]
    assert after["stotra_saraswati_mercury_education"]["classical_ref"] == "modern devotional practice (Sarasvatī for Budha)"
    s = after["dosha_sade_sati_shani_charity"]
    assert s["prescription_text"].startswith("Classical Saturn dāna per BPHS Ch.84 §25: a black cow (bphs:PG999:C1).")
    assert s["classical_ref"] == "BPHS Ch.84 §25 — bphs:PG999:C1 (black cow); remainder modern"


def test_punarphoo_absorbs_vish_dosha_without_the_pearl_advice(after, before):
    p = after["dosha_punarphoo_shani_mantra"]
    assert "Mahāmṛtyuñjaya japa; Śiva pūjā on Mondays" in p["prescription_text"]
    assert p["domain"] == "general" and before["dosha_punarphoo_shani_mantra"]["domain"] == "marriage"
    assert "No blanket gem advice" in p["contraindications"]
    assert "Pearl" not in p["prescription_text"]
    assert "NAME COLLISION" in p["source_citation"]
    assert "dosha_vish_dosha_shani_chandra" not in after


def test_mrityu_bhaga_and_angarak_labels(after):
    assert "project parameter" in after["dosha_mrityu_bhaga_mantra"]["prescription_text"]
    assert "modern practice" in after["dosha_angarak_mars_rahu"]["prescription_text"]


# ---- the overlay fails loudly ---------------------------------------------------------------------------------------

def test_overlay_raises_when_a_decided_key_is_not_produced():
    rows = [r for r in _pre_overlay_rows().values() if r["remedy_id"] != "dosha_yoni_puja"]
    with pytest.raises(RuntimeError, match="dosha_yoni_puja"):
        C.apply_pass2(rows)


def test_overlay_does_not_mutate_the_module_level_seed_rows():
    snapshot = [dict(r) for r in L.DOSHA_REMEDIES]
    L.build_all_remedies()
    L.build_all_remedies()
    assert [r for r in L.DOSHA_REMEDIES if r["remedy_id"] in REMOVED]                    # the removed rows still exist in the seed list, only filtered out
    assert [{k: v for k, v in r.items() if k != "remedy_type"} for r in L.DOSHA_REMEDIES] == [{k: v for k, v in r.items() if k != "remedy_type"} for r in snapshot]


def test_source_distribution_after_overlay(after):
    c = Counter(r["source_canonical_id"] for r in after.values())
    assert c["k2:OS-2026-10-05-CITATIONS"] == 45 and c["bphs"] == 29 and c["muhurta_chintamani"] == 1 and c["k1_unverified"] == 1


# ---- the expected-change declaration for the dispatch tool ----------------------------------------------------------

def test_expected_change_file_matches_the_seed_and_the_dispatch_tool_shape(after):
    import json
    import pathlib
    p = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE" / "control" / "expected_change" / "EXPECTED_CHANGE_bg_remedies_citation_pass2.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    assert set(d) <= {"asset", "expected_post_row_count", "expected_post_fingerprint", "why", "decision", "evidence", "excluded_tables_acknowledged"}
    assert d["asset"] == "bg_remedies"
    assert d["expected_post_row_count"] == len(after) + 54 + 4 == 316          # static rows + corpus-sweep rows + accepted tantric rows
    assert d["decision"] == K2_ID and re.fullmatch(r"([A-Za-z]{1,4})-?([0-9]{1,6})[A-Za-z0-9._-]{0,24}", d["decision"])
    assert d["excluded_tables_acknowledged"] == ["remedy_review_queue"]
    assert 15 <= len(d["why"]) <= 500 and 10 <= len(d["evidence"]) <= 500
    assert "expected_post_fingerprint" not in d or d["expected_post_fingerprint"] is None
