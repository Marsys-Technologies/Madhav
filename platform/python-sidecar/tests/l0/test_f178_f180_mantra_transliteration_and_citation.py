"""
test_f178_f180_mantra_transliteration_and_citation.py
=====================================================

Standing guards for PARIŚEṢA-V4 **F-178** (`brahmagyan/remedy_corpus/mantras.yaml`)
and **F-180** (`00_ARCHITECTURE/CONDUCTOR/ws3/bphs_canon_batch_04.yaml`).

Authority: `00_ARCHITECTURE/briefs/parisesa/OWNER_RULINGS_20260821.md`, rulings R-1
(Saturn's bīja completion is *śanaiścarāya*, not *śanaye* — a different, shorter
mantra) and R-2 (the tantric `prāṃ prīṃ prauṃ saḥ` bīja class must not be attributed
to BPHS). Both defects were already corrected in the live-served Python corpus by
PR #1429 (`brahmagyan/l0_remedy_corpus.py`); GA-5 review of that PR found the same
defect class in these two further, independently-loaded files.

Per CLAUDE.md §N.7 item 2 and §N.8, the assertions below are **computations over each
row's own two script fields**, not golden strings: a Devanagari→IAST transliterator
derives what the row's `mantra_sanskrit` actually says, and a documented romanisation
fold compares that against the row's stored `mantra_transliteration`. A row whose two
fields disagree fails, whatever the disagreement is.

Honest scope of the detector (§N.8 — say what the signal does and does not measure):

  * The fold is deliberately **vowel-length- and sibilant-insensitive**, because this
    corpus's own ASCII romanisation is not internally consistent about either
    (`sūryāya`→"Suryaya" drops the length, `prāṃ`→"Praam" keeps it). It therefore
    catches wrong-word and wrong-consonant defects (śanaye/śanaiścarāya,
    Guruve/Gurave, Buddhaya/Budhaya, Ahukethavah/Ahuketavah) but would NOT catch a
    length-only deviation. Length-only corrections in this wave (Bhram→Bhraam,
    Sram→Sraam) are therefore additionally pinned by explicit assertions below.
  * `mantras.yaml` is NOT migrated to the R-4 IAST column contract — see the header
    comment in that file for why (the column feeds the DB's recitation-ready
    `mantra_text`). So this file asserts *script coherence*, not IAST conformance.
    The IAST conformance guard for the Python corpus lives in PR #1429's
    `test_f23_mantra_script_and_citation.py`.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml


# ── Paths ────────────────────────────────────────────────────────────────────

_SIDECAR = Path(__file__).resolve().parents[2]                 # platform/python-sidecar
MANTRAS_YAML = _SIDECAR / "brahmagyan" / "remedy_corpus" / "mantras.yaml"
WS3_DIR = _SIDECAR.parents[1] / "00_ARCHITECTURE" / "CONDUCTOR" / "ws3"
BATCH_04_YAML = WS3_DIR / "bphs_canon_batch_04.yaml"


# ── Devanagari → IAST ────────────────────────────────────────────────────────
# Deterministic and table-driven; anything outside the tables raises, so an
# unhandled character is a loud failure rather than a silent pass. Same tables as
# PR #1429's F-23 guard — duplicated rather than imported because that module is on
# a separate unmerged branch; the two must stay in agreement.

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
    "ं": "ṃ", "ः": "ḥ", "ँ": "m̐", "ऽ": "'", "ॐ": "oṃ",
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
            if i < n and text[i] == _VIRAMA:
                i += 1                                  # virāma: no vowel at all
            elif i < n and text[i] in _MATRAS:
                out.append(_MATRAS[text[i]])
                i += 1
            else:
                out.append("a")                         # inherent 'a'
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


# ── Romanisation fold ────────────────────────────────────────────────────────
# Collapses IAST and this corpus's ASCII romanisation onto one alphabet so the two
# can be compared. Order is load-bearing and each step is stated:
#   1. diacritics → their ASCII digraph (ś/ṣ→"sh", ṛ→"ri", ṃ→"m", ḥ→"h", …)
#   2. "ch"→"c" and "sh"→"s"   (IAST `c`/`ś` and ASCII "ch"/"sh" write one sound)
#   3. drop everything that is not a letter (spaces, hyphens, punctuation) — this has
#      to precede step 4 so that a hyphenated compound written without its sandhi
#      ("Bhuta-Atma") folds onto the sandhi'd Devanagari (भूतात्मा, bhūtātmā)
#   4. doubled vowels → single ("aa"→"a", "ee"→"i", "oo"/"uu"→"u", "ii"→"i")
#   5. diphthongs → single tokens ("ai"→"E", "au"→"O") so they stay distinct from
#      the plain vowels step 4 produced

_DIACRITICS = [
    ("m̐", "m"), ("ā", "a"), ("ī", "i"), ("ū", "u"),
    ("ṝ", "ri"), ("ṛ", "ri"), ("ḹ", "li"), ("ḷ", "l"),
    ("ṃ", "m"), ("ṁ", "m"), ("ḥ", "h"),
    ("ś", "sh"), ("ṣ", "sh"), ("ñ", "n"), ("ṅ", "n"), ("ṇ", "n"),
    ("ṭ", "t"), ("ḍ", "d"),
]


def fold(s: str) -> str:
    """Fold IAST or corpus-ASCII romanisation onto one comparable alphabet."""
    s = s.lower()
    for a, b in _DIACRITICS:
        s = s.replace(a, b)
    s = s.replace("ch", "c").replace("sh", "s")
    s = re.sub(r"[^a-z]", "", s)
    for a, b in [("aa", "a"), ("ee", "i"), ("oo", "u"), ("ii", "i"), ("uu", "u")]:
        s = s.replace(a, b)
    return s.replace("ai", "E").replace("au", "O")


# Rows whose romanisation is legitimately not a Sanskrit transliteration of their
# own Devanagari. Pinned, with the reason — so a NEW non-conforming row fails rather
# than quietly joining an open-ended exemption.
KNOWN_NON_SANSKRIT_ROWS: dict[str, str] = {
    "mnt_hanuman_chalisa_015":
        "Tulsīdās's Hanumān Cālīsā is Awadhi/Hindi, not Sanskrit: the stored form "
        "carries Hindi schwa-deletion (sāgara→'Sagar', hanumāna→'Hanuman'), "
        "jaya→'Jai', and jña→'Gya'. Correct as recited; not a Sanskrit round-trip.",
}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def mantra_rows() -> list[dict]:
    rows = yaml.safe_load(MANTRAS_YAML.read_text(encoding="utf-8"))
    assert isinstance(rows, list) and rows, "mantras.yaml must parse to a non-empty list"
    return rows


@pytest.fixture(scope="module")
def bija_rows(mantra_rows) -> list[dict]:
    rows = [r for r in mantra_rows if "beeja" in r["remedy_id"]]
    assert len(rows) == 9, f"expected 9 navagraha bīja rows, got {len(rows)}"
    return rows


@pytest.fixture(scope="module")
def mantra_rule_82_8_1() -> dict:
    data = yaml.safe_load(BATCH_04_YAML.read_text(encoding="utf-8"))
    matches = [r for r in data["rules"] if r and r.get("rule_id") == "BPHS.82.8.1"]
    assert len(matches) == 1, f"expected exactly 1 BPHS.82.8.1 rule, got {len(matches)}"
    return matches[0]


# ── The detector must itself be checked ──────────────────────────────────────

class TestDetector:
    @pytest.mark.parametrize("deva,iast", [
        ("ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः", "oṃ prāṃ prīṃ prauṃ saḥ śanaiścarāya namaḥ"),
        ("ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः", "oṃ grāṃ grīṃ grauṃ saḥ gurave namaḥ"),
        ("ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः", "oṃ brāṃ brīṃ brauṃ saḥ budhāya namaḥ"),
    ])
    def test_transliterator_known_pairs(self, deva, iast):
        assert devanagari_to_iast(deva) == iast

    def test_transliterator_rejects_unmapped_character(self):
        with pytest.raises(ValueError):
            devanagari_to_iast("ॐ नमः ☃")

    @pytest.mark.parametrize("deva,stale", [
        # R-1: the śanaye contamination — a different, shorter mantra.
        ("ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः", "Om Praam Preem Praum Sah Shanaye Namah"),
        # F-178 sweep: Jupiter's dative is गुरवे (gurave), not "Guruve".
        ("ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः", "Om Graam Greem Graum Sah Guruve Namah"),
        # F-180 second defect: Mercury is बुधाय (Budhaya), not "Buddhaya".
        ("ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः", "Om Braam Breem Braum Sah Buddhaya Namah"),
    ])
    def test_fold_rejects_each_pre_fix_pair(self, deva, stale):
        """Every defect this PR fixes must be one the fold actually detects."""
        assert fold(devanagari_to_iast(deva)) != fold(stale)

    @pytest.mark.parametrize("deva,fixed", [
        ("ॐ प्रां प्रीं प्रौं सः शनैश्चराय नमः", "Om Praam Preem Praum Sah Shanaischaraya Namah"),
        ("ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः", "Om Graam Greem Graum Sah Gurave Namah"),
        ("ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः", "Om Braam Breem Braum Sah Budhaya Namah"),
    ])
    def test_fold_accepts_each_post_fix_pair(self, deva, fixed):
        assert fold(devanagari_to_iast(deva)) == fold(fixed)


# ── F-178 · R-1 class: script coherence across mantras.yaml ──────────────────

class TestMantrasYamlScriptCoherence:
    def test_every_row_transliteration_matches_its_own_devanagari(self, mantra_rows):
        failures: list[str] = []
        checked = 0
        for r in mantra_rows:
            deva, translit = r.get("mantra_sanskrit"), r.get("mantra_transliteration")
            if not deva or not translit:
                continue
            if r["remedy_id"] in KNOWN_NON_SANSKRIT_ROWS:
                continue
            checked += 1
            try:
                derived = devanagari_to_iast(deva)
            except ValueError as exc:
                failures.append(f"{r['remedy_id']}: untransliterable — {exc}")
                continue
            if fold(derived) != fold(translit):
                failures.append(
                    f"{r['remedy_id']}: sanskrit says {derived!r} "
                    f"but transliteration says {translit!r}"
                )
        assert failures == [], (
            "mantra_sanskrit / mantra_transliteration disagree:\n  "
            + "\n  ".join(failures)
        )
        assert checked >= 17, (
            f"expected at least 17 dual-script rows to be covered, got {checked} — "
            f"the guard must not silently stop covering rows"
        )

    def test_pinned_exemptions_still_match_a_real_row(self, mantra_rows):
        ids = {r["remedy_id"] for r in mantra_rows}
        stale = sorted(set(KNOWN_NON_SANSKRIT_ROWS) - ids)
        assert stale == [], f"exemption listed for rows that no longer exist: {stale}"

    def test_no_row_carries_the_shanaye_bija_contamination(self, mantra_rows):
        offenders = [
            r["remedy_id"] for r in mantra_rows
            if "shanaye" in " ".join(str(v) for v in r.values()).lower()
        ]
        assert offenders == [], f"stale 'Shanaye' bīja form still present: {offenders}"

    @pytest.mark.parametrize("remedy_id,expected", [
        # Length-only corrections: the fold is length-insensitive by design, so these
        # are pinned explicitly rather than left to a guard that cannot see them.
        ("mnt_rahu_beeja_009", "Om Bhraam Bhreem Bhraum Sah Rahave Namah"),
        ("mnt_ketu_beeja_010", "Om Sraam Sreem Sraum Sah Ketave Namah"),
    ])
    def test_vowel_length_corrections_are_pinned(self, mantra_rows, remedy_id, expected):
        row = next(r for r in mantra_rows if r["remedy_id"] == remedy_id)
        assert row["mantra_transliteration"] == expected


# ── F-178 · R-2 class: the 9 bīja rows must not be attributed to BPHS ────────

class TestMantrasYamlBijaAttribution:
    def test_bija_rows_cite_the_navagraha_bija_tradition(self, bija_rows):
        for r in bija_rows:
            ref = f"{r['source_chapter']} {r['source_verse']}"
            assert "Navagraha bīja tradition" in ref, f"{r['remedy_id']}: {ref}"
            assert "Mantra Mahodadhi" in ref, f"{r['remedy_id']}: {ref}"

    def test_bija_rows_label_bphs_as_upaya_context_only(self, bija_rows):
        for r in bija_rows:
            ref = f"{r['source_chapter']} {r['source_verse']}"
            if "BPHS" in ref:
                assert "upāya context only" in ref, (
                    f"{r['remedy_id']} cites BPHS without the upāya-context label: {ref}"
                )
            assert not str(r["source_chapter"]).startswith("BPHS"), (
                f"{r['remedy_id']} leads its citation with BPHS, implying it is the source"
            )

    def test_bija_rows_do_not_name_bphs_as_the_canonical_source(self, bija_rows):
        # `source_text` is what l0_remedy_loader maps to `source_canonical_id`.
        for r in bija_rows:
            assert r["source_text"] != "BPHS", r["remedy_id"]

    def test_bija_rows_carry_no_verbatim_quotation(self, bija_rows):
        """
        R-2 + R-4 + §N.7 item 6: the fabricated `BPHS Ch.91 v.NN: '...'` quotation is
        removed, and NOT replaced with an invented quotation from another edition. A
        quoted span in this field is exactly the defect F-178 names.
        """
        for r in bija_rows:
            attest = r["classical_attestation_text"]
            assert attest, f"{r['remedy_id']}: attestation must state the gap, not be blank"
            assert "No verbatim classical attestation located" in attest, r["remedy_id"]
            assert "'" not in attest and '"' not in attest, (
                f"{r['remedy_id']} still carries a quoted span: {attest!r}"
            )
            assert not re.search(r"BPHS Ch\.\d+ v\.", attest), (
                f"{r['remedy_id']} still cites a BPHS chapter-and-verse for the bīja: {attest!r}"
            )

    def test_classical_ref_agrees_with_the_python_corpus_constant(self, bija_rows):
        """
        `l0_remedy_loader` builds `classical_ref` as f"{source_chapter} {source_verse}".
        PR #1429 corrects the same 9 bīja rows in `l0_remedy_corpus.py` under the same
        ruling, via `CLASSICAL_REF_BIJA`. Both corpora feed the same table, so a row's
        citation must not depend on which loader seeded it. Asserted against the other
        module's constant rather than a golden string — so the two cannot drift apart
        without this failing.
        """
        from brahmagyan import l0_remedy_corpus
        expected = getattr(l0_remedy_corpus, "CLASSICAL_REF_BIJA", None)
        if expected is None:
            pytest.skip(
                "CLASSICAL_REF_BIJA lands with PR #1429 (F-23 R-2) and is not on this "
                "base yet; this assertion activates automatically once that merges"
            )
        for r in bija_rows:
            built = f"{r['source_chapter']} {r['source_verse']}".strip()
            assert built == expected, f"{r['remedy_id']}: {built!r} != {expected!r}"

    def test_attestation_survives_the_loaders_source_citation_truncation(self, bija_rows):
        """l0_remedy_loader stores `classical_attestation_text[:500]` as source_citation."""
        for r in bija_rows:
            assert len(r["classical_attestation_text"]) <= 500, r["remedy_id"]

    def test_non_bija_rows_are_untouched_by_the_reattribution(self, mantra_rows):
        """R-2 scopes to the bīja class only — stotra/nāma rows keep their citations."""
        gayatri = next(r for r in mantra_rows if r["remedy_id"] == "mnt_gayatri_012")
        assert gayatri["source_text"] == "BPHS"
        assert gayatri["mantra_transliteration"].startswith("Om Bhur Bhuvah Svah")


# ── F-180: bphs_canon_batch_04.yaml ──────────────────────────────────────────

class TestBatch04MantraRule:
    def test_saturn_bija_uses_shanaischaraya(self, mantra_rule_82_8_1):
        assertion = mantra_rule_82_8_1["assertion"]
        assert "Sah Shanaischaraya Namah" in assertion
        assert "Shanaye" not in assertion

    def test_mercury_bija_uses_budhaya(self, mantra_rule_82_8_1):
        assertion = mantra_rule_82_8_1["assertion"]
        assert "Sah Budhaya Namah" in assertion
        assert "Buddhaya" not in assertion

    def test_every_bija_in_the_assertion_matches_the_yaml_corpus_devanagari(
        self, mantra_rule_82_8_1, mantra_rows
    ):
        """
        Cross-corpus coherence, computed rather than pinned: each `Om ... Namah` string
        this rule asserts is folded against the Devanagari its planet carries in
        `mantras.yaml`. Two independently-maintained corpora must not drift.
        """
        deva_by_planet = {
            r["planet"]: r["mantra_sanskrit"]
            for r in mantra_rows if "beeja" in r["remedy_id"]
        }
        quoted = re.findall(
            r'(\w+)\s*=\s*"(Om [^"]*Namah)"',
            re.sub(r"\s+", " ", mantra_rule_82_8_1["assertion"]),
        )
        assert len(quoted) == 7, f"expected 7 planet bījas in the rule, got {len(quoted)}"
        failures = []
        for planet, romanised in quoted:
            deva = deva_by_planet.get(planet)
            assert deva, f"no mantras.yaml bīja row for {planet}"
            if fold(devanagari_to_iast(deva)) != fold(romanised):
                failures.append(
                    f"{planet}: batch_04 says {romanised!r} but mantras.yaml Devanagari "
                    f"says {devanagari_to_iast(deva)!r}"
                )
        assert failures == [], "cross-corpus bīja drift:\n  " + "\n  ".join(failures)

    def test_caveats_carry_the_r2_attribution_correction(self, mantra_rule_82_8_1):
        caveats = mantra_rule_82_8_1["caveats"]
        assert "Mantra Mahodadhi" in caveats
        assert "upāya context for this rule, not the source of the bīja strings" in caveats

    def test_load_bearing_identifiers_are_unchanged(self, mantra_rule_82_8_1):
        """
        `l2_remediation_grounded.py` pins rule_id BPHS.82.8.1 and verse 82.8, and
        `_grounding_engine.py` cites `source_verse.verse_ref` to users. A future pass
        must not "fix" the attribution by renaming the rule out from under them.
        """
        assert mantra_rule_82_8_1["rule_id"] == "BPHS.82.8.1"
        assert mantra_rule_82_8_1["source_verse"]["canonical_id"] == "BPHS"
        assert mantra_rule_82_8_1["source_verse"]["verse_ref"] == "82.8"
        assert mantra_rule_82_8_1["scope"] == "remedy"
        assert mantra_rule_82_8_1["confidence"] == 0.80

    def test_file_still_loads_through_the_live_grounding_engine(self):
        """
        The edit must not break the `*.yaml` glob load that serves this corpus. The
        engine swallows per-file exceptions, so a YAML break would show up only as a
        silently missing rule — assert the rule is actually present after loading.
        """
        from brahmagyan.bodha._grounding_engine import load_all_rules
        rules = load_all_rules()
        by_id = [r for r in rules if r and r.get("rule_id") == "BPHS.82.8.1"]
        assert len(by_id) == 1, (
            f"BPHS.82.8.1 not loaded exactly once by load_all_rules() ({len(by_id)}) — "
            f"bphs_canon_batch_04.yaml may have stopped parsing"
        )
        assert "Shanaischaraya" in by_id[0]["assertion"]

    def test_short_nama_mantra_form_elsewhere_in_ws3_is_not_collateral_damage(self):
        """
        R-1 is explicit that `Om Shanaye Namah` is a REAL mantra — the short
        nāma-mantra — and only wrong as the completion of the bīja string. The ws3
        nāma-mantra lists that carry it correctly must survive this wave untouched.
        """
        pilot = (WS3_DIR / "bphs_pilot_rules.yaml").read_text(encoding="utf-8")
        assert "Saturn: 'Om Shanaye Namah'" in pilot
        assert "Om Praam Preem Praum Sah Shanaye Namah" not in pilot
