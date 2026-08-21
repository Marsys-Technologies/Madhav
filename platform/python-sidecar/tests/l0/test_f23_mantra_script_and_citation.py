"""
test_f23_mantra_script_and_citation.py — standing guards for PARIŚEṢA-V4 F-23.

Authority: `00_ARCHITECTURE/briefs/parisesa/OWNER_RULINGS_20260821.md`, rulings
R-1 / R-2 / R-3 (and the R-4 column contract they are executed under).

Two defect classes were caught by hand in F-23. Both are turned into detectors
here rather than left as one-off corrections, per CLAUDE.md §N.7 item 2 and
§N.8 (a status/claim needs a detector that measures the specific claim, or it is
not earned):

  1. **Script incoherence.** `saturn_matrix_mantra` stored Devanagari
     `ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः` (*śanaiścarāya*) against transliteration
     `"Om Praam Preem Praum Sah Shanaye Namah"` (*śanaye*) — two different words on
     one row. The guard below is a real Devanagari→IAST transliterator, so the
     assertion is a computation over the row's own two fields, not a golden string.

  2. **Citation overclaim.** The 9 bīja rows attributed the `prāṃ prīṃ prauṃ saḥ`
     mantra class to BPHS Ch.91-94 (R-2: incorrect-as-stated), and the 27 nakshatra
     rows cited BPHS Ch.94 in a way that implied BPHS supplies the mantra text when
     it supplies only the devatā (R-3).

Scope note (honest, not a silent skip): the IAST round-trip is asserted over every
row `build_all_remedies()` emits that carries BOTH `mantra_sanskrit` and
`mantra_transliteration`. Rows that predate the R-4 contract and still use an
ad-hoc ASCII romanisation are listed explicitly in `KNOWN_NON_IAST_ROWS` with the
reason — the list is pinned, so a NEW non-conforming row fails the test rather
than quietly joining an open-ended exemption.
"""
from __future__ import annotations

import re

import pytest


# ── Devanagari → IAST ─────────────────────────────────────────────────────────
# Deterministic, table-driven. Covers the subset of Devanagari the remedy corpus
# uses (no Vedic accents, no nukta consonants); anything outside the tables raises,
# so an unhandled character is a loud failure, never a silent pass.

_INDEPENDENT_VOWELS = {
    "अ": "a", "आ": "ā", "इ": "i", "ई": "ī", "उ": "u", "ऊ": "ū",
    "ऋ": "ṛ", "ॠ": "ṝ", "ऌ": "ḷ", "ॡ": "ḹ",
    "ए": "e", "ऐ": "ai", "ओ": "o", "औ": "au",
}

_MATRAS = {
    "ा": "ā", "ि": "i", "ी": "ī", "ु": "u", "ू": "ū",
    "ृ": "ṛ", "ॄ": "ṝ", "ॢ": "ḷ", "ॣ": "ḹ",
    "े": "e", "ै": "ai", "ो": "o", "ौ": "au",
}

_CONSONANTS = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "ṅ",
    "च": "c", "छ": "ch", "ज": "j", "झ": "jh", "ञ": "ñ",
    "ट": "ṭ", "ठ": "ṭh", "ड": "ḍ", "ढ": "ḍh", "ण": "ṇ",
    "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m",
    "य": "y", "र": "r", "ल": "l", "ळ": "ḷ", "व": "v",
    "श": "ś", "ष": "ṣ", "स": "s", "ह": "h",
}

_SIGNS = {
    "ं": "ṃ",    # anusvāra
    "ः": "ḥ",    # visarga
    "ँ": "m̐",    # candrabindu
    "ऽ": "'",    # avagraha
    "ॐ": "oṃ",   # oṃkāra ligature
    "।": ".", "॥": ".",
}

_VIRAMA = "्"
_PASSTHROUGH = set(" \t\n.,;:-—()'\"/")


def devanagari_to_iast(text: str) -> str:
    """Transliterate Devanagari to IAST. Raises ValueError on unknown characters."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in _SIGNS:
            out.append(_SIGNS[ch])
            i += 1
        elif ch in _INDEPENDENT_VOWELS:
            out.append(_INDEPENDENT_VOWELS[ch])
            i += 1
        elif ch in _CONSONANTS:
            out.append(_CONSONANTS[ch])
            i += 1
            # inherent 'a' unless a virāma or an explicit mātrā follows
            if i < n and text[i] == _VIRAMA:
                i += 1                      # virāma: no vowel at all
            elif i < n and text[i] in _MATRAS:
                out.append(_MATRAS[text[i]])
                i += 1
            else:
                out.append("a")
        elif ch in _MATRAS:
            raise ValueError(f"stray mātrā {ch!r} at index {i} in {text!r}")
        elif ch == _VIRAMA:
            raise ValueError(f"stray virāma at index {i} in {text!r}")
        elif ch in _PASSTHROUGH:
            out.append(ch)
            i += 1
        else:
            raise ValueError(f"unmapped character {ch!r} (U+{ord(ch):04X}) in {text!r}")
    return "".join(out)


def _norm(s: str) -> str:
    """Collapse whitespace for comparison; script content must match exactly."""
    return re.sub(r"\s+", " ", s).strip()


# Rows that carry both script fields but predate the R-4 column contract
# (`mantra_transliteration` = IAST). Pinned deliberately — F-23 Lane 2 owns the
# backfill; until then these are declared, not hidden.
KNOWN_NON_IAST_ROWS: dict[str, str] = {
    "stotra_mahamrityunjaya_saturn_affliction":
        "ad-hoc ASCII romanisation of the Mahāmṛtyuñjaya ṛk; F-23 Lane 2 backfill",
}


def _built_rows():
    from brahmagyan.l0_remedy_corpus import build_all_remedies
    return build_all_remedies()


def _by_id(rows, remedy_id):
    matches = [r for r in rows if r["remedy_id"] == remedy_id]
    assert len(matches) == 1, f"expected exactly 1 row {remedy_id}, got {len(matches)}"
    return matches[0]


# ── Transliterator self-test (the detector must itself be checked) ────────────

class TestTransliterator:
    @pytest.mark.parametrize("deva,iast", [
        ("ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः", "oṃ prāṃ prīṃ prauṃ saḥ śanaiścarāya namaḥ"),
        ("ॐ श्रां श्रीं श्रौं सः चन्द्राय नमः", "oṃ śrāṃ śrīṃ śrauṃ saḥ candrāya namaḥ"),
        ("ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः", "oṃ hrāṃ hrīṃ hrauṃ saḥ sūryāya namaḥ"),
    ])
    def test_known_pairs(self, deva, iast):
        assert devanagari_to_iast(deva) == iast

    def test_rejects_unmapped_character(self):
        with pytest.raises(ValueError):
            devanagari_to_iast("ॐ नमः ☃")

    def test_detects_the_original_f23_defect(self):
        """The pre-fix Saturn pair MUST fail — proves the guard has teeth."""
        deva = "ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः"
        stale = "Om Praam Preem Praum Sah Shanaye Namah"
        assert _norm(devanagari_to_iast(deva)) != _norm(stale)


# ── R-1 + R-4: script coherence across the corpus ────────────────────────────

class TestScriptCoherence:
    def test_saturn_bija_transliteration_is_the_ruled_iast(self):
        """Owner ruling R-1, verbatim target value."""
        row = _by_id(_built_rows(), "saturn_matrix_mantra")
        assert row["mantra_sanskrit"] == "ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः"
        assert row["mantra_transliteration"] == "oṃ prāṃ prīṃ prauṃ saḥ śanaiścarāya namaḥ"

    def test_no_row_anywhere_still_says_shanaye(self):
        """The śanaye contamination must be gone from every field, prose included."""
        offenders = [
            r["remedy_id"] for r in _built_rows()
            if any(
                "shanaye" in str(v).lower()
                for k, v in r.items()
                if k in {
                    "prescription_text", "mantra_text", "mantra_sanskrit",
                    "mantra_transliteration", "charity_action",
                }
            )
        ]
        assert offenders == [], f"stale 'Shanaye' bīja form still present: {offenders}"

    def test_every_dual_script_row_round_trips_to_iast(self):
        """
        For every built row carrying both script fields, the transliteration must be
        the IAST rendering of its own Devanagari. This is the general invariant the
        F-23 Saturn defect violated.
        """
        failures: list[str] = []
        checked = 0
        for r in _built_rows():
            deva = r.get("mantra_sanskrit")
            translit = r.get("mantra_transliteration")
            if not deva or not translit:
                continue
            if r["remedy_id"] in KNOWN_NON_IAST_ROWS:
                continue
            checked += 1
            try:
                expected = devanagari_to_iast(deva)
            except ValueError as exc:                       # pragma: no cover
                failures.append(f"{r['remedy_id']}: untransliterable — {exc}")
                continue
            if _norm(expected) != _norm(translit):
                failures.append(
                    f"{r['remedy_id']}: sanskrit→{_norm(expected)!r} "
                    f"but transliteration={_norm(translit)!r}"
                )
        assert failures == [], "Devanagari/IAST mismatch:\n  " + "\n  ".join(failures)
        assert checked >= 18, (
            f"expected at least the 18 navagraha bīja matrix rows to be covered, "
            f"got {checked} — the guard must not silently stop covering rows"
        )

    def test_every_navagraha_matrix_row_transliterates_in_iast(self):
        """
        `gen_planet_matrix()` interpolates the same romanised bīja into three cells
        per planet — mantra, japa and yantra. The F-23 reproducer only counted
        `remedy_type='mantra'`, so the japa and yantra siblings carried the identical
        śanaye defect invisibly. All three must satisfy the R-4 contract.
        """
        rows = [
            r for r in _built_rows()
            if "_matrix_" in r["remedy_id"] and r.get("mantra_transliteration")
        ]
        assert len(rows) == 27, (
            f"expected 27 navagraha matrix rows carrying a transliteration "
            f"(9 planets x mantra/japa/yantra), got {len(rows)}"
        )
        offenders = [
            r["remedy_id"] for r in rows
            if not r["mantra_transliteration"].startswith("oṃ ")
        ]
        assert offenders == [], f"non-IAST transliteration on matrix rows: {offenders}"

    def test_known_non_iast_exemptions_still_exist(self):
        """A pinned exemption that no longer matches a row is a stale exemption."""
        ids = {r["remedy_id"] for r in _built_rows()}
        stale = sorted(set(KNOWN_NON_IAST_ROWS) - ids)
        assert stale == [], f"exemption listed for rows that no longer exist: {stale}"


# ── R-2: the 9 bīja rows must not attribute the mantra to BPHS ───────────────

class TestBijaAttribution:
    def _bija_rows(self):
        rows = [r for r in _built_rows() if r["remedy_id"].endswith("_matrix_mantra")]
        assert len(rows) == 9, f"expected 9 bīja-matrix rows, got {len(rows)}"
        return rows

    def test_nine_bija_rows_cite_the_navagraha_bija_tradition(self):
        for r in self._bija_rows():
            ref = r["classical_ref"]
            assert "Navagraha bīja tradition" in ref, f"{r['remedy_id']}: {ref}"
            assert "Mantra Mahodadhi" in ref, f"{r['remedy_id']}: {ref}"

    def test_bija_rows_label_bphs_as_upaya_context_only(self):
        """
        BPHS may still be referenced — but only as upāya context, explicitly labelled,
        never as the mantra's source (owner ruling R-2).
        """
        for r in self._bija_rows():
            ref = r["classical_ref"]
            if "BPHS" in ref:
                assert "upāya context only" in ref, (
                    f"{r['remedy_id']} cites BPHS without the upāya-context label: {ref}"
                )
                assert not ref.startswith("BPHS"), (
                    f"{r['remedy_id']} leads with BPHS, implying it is the source: {ref}"
                )

    def test_bija_rows_do_not_claim_bphs_as_source_citation(self):
        for r in self._bija_rows():
            assert r["source_canonical_id"] != "BPHS", r["remedy_id"]
            assert "Navagraha bīja tradition" in r["source_citation"], r["remedy_id"]


# ── R-3: the 27 nakshatra rows must not overclaim BPHS Ch.94 ─────────────────

class TestNakshatraAttribution:
    def _nakshatra_rows(self):
        rows = [
            r for r in _built_rows()
            if r["remedy_id"].startswith("nakshatra_")
            and r["remedy_id"].endswith("_mantra")
            and r.get("remedy_type") == "mantra"
        ]
        assert len(rows) == 27, f"expected 27 nakshatra mantra rows, got {len(rows)}"
        return rows

    def test_citation_states_devata_attribution_only(self):
        for r in self._nakshatra_rows():
            ref = r["classical_ref"]
            assert "devatā attribution" in ref, f"{r['remedy_id']}: {ref}"

    def test_citation_labels_the_mantra_form_as_constructed(self):
        for r in self._nakshatra_rows():
            ref = r["classical_ref"]
            assert "nāma-mantra form (constructed)" in ref, f"{r['remedy_id']}: {ref}"

    def test_citation_does_not_bare_cite_bphs_ch94(self):
        """`BPHS Ch.94` unqualified is the exact overclaim R-3 removes."""
        for r in self._nakshatra_rows():
            ref = r["classical_ref"]
            assert not re.search(r"BPHS Ch\.94(?!\s*\(devatā attribution\))", ref), (
                f"{r['remedy_id']} cites BPHS Ch.94 without scoping it to the devatā: {ref}"
            )

    def test_nama_mantra_text_is_retained_as_the_served_form(self):
        """
        R-3 corrects the CITATION only — the recitable nāma-mantra stays primary.
        Regression guard against a future pass 'fixing' this by deleting the mantra.
        """
        row = _by_id(self._nakshatra_rows(), "nakshatra_anuradha_mantra")
        assert row["mantra_transliteration"] == "Om Mitraya Namah"
        assert "Om Mitraya Namah" in row["prescription_text"]
        assert row["deity"] == "Mitra"
