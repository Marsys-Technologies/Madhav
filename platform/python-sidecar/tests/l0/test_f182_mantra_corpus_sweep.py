"""
test_f182_mantra_corpus_sweep.py
================================

Standing guard for PARIŚEṢA-V4 **F-182** — the corpus-wide sweep that follows
F-23 (PR #1429, the 9 bīja *matrix* rows) and F-178/F-180 (`mantras.yaml`,
`bphs_canon_batch_04.yaml`) for the SAME two defect classes, on every remaining
surface: the domain-scaffold rows in `brahmagyan/l0_remedy_corpus.py`, eight
`remedy_corpus/*.yaml` files, and the two in-code fixture modules
`bodha/l2_remediation_grounded.py` and `phala/l4_mitigation.py`.

Authority: `00_ARCHITECTURE/briefs/parisesa/state/OWNER_RULINGS_20260821.md`

  R-1  Where a row's Devanagari and its transliteration disagree, the Devanagari
       decides. Internal consistency settles it — no scholarly judgment needed.
  R-2  The `prāṃ prīṃ prauṃ saḥ` navagraha bīja class is NOT BPHS material.
       Reattribute to the Navagraha bīja tradition / Mantra Mahodadhi; BPHS may
       remain only as explicitly-labelled `upāya context`.

WHAT THE DETECTOR ACTUALLY MEASURES (CLAUDE.md §N.8 — say what the signal does
and does not claim):

  * The bīja assertions are a **computation against the corpus's own canonical
    table**, `PLANET_REMEDY_DATA[planet]['beej']`, whose own coherence is in turn
    asserted here against its own Devanagari via the F-178 guard's Devanagari→IAST
    transliterator. Nothing in this file is a hand-typed golden mantra string, so
    the guard cannot drift into pinning a wrong value.
  * That comparison is **exact, not folded** — deliberately. The F-178 guard's
    romanisation `fold()` is vowel-length-insensitive and therefore could not have
    caught this wave's dominant defect (`Bhram`→`Bhraam`, `Sram`→`Sraam`). Exact
    comparison against the canonical ASCII form catches length, wrong-word
    (`Guruve`→`Gurave`) and wrong-graha (Sun's `Hraam Hreem Hraum` served under
    Saturn's name) alike.
  * It does NOT check mantras outside the navagraha bīja class, and does not
    verify the classical attestation of any citation — only that the *bīja class*
    stops claiming BPHS as its source.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

# Reuse — not re-implement — the Devanagari→IAST transliterator that the merged
# F-178/F-180 guard already carries. If the two ever disagree, this import makes
# it a loud failure in one place rather than a silent divergence in two.
from tests.l0.test_f178_f180_mantra_transliteration_and_citation import (
    devanagari_to_iast,
)


_SIDECAR = Path(__file__).resolve().parents[2]           # platform/python-sidecar
_CORPUS_YAML_DIR = _SIDECAR / "brahmagyan" / "remedy_corpus"
_L2_FIXTURES = _SIDECAR / "brahmagyan" / "bodha" / "l2_remediation_grounded.py"
_L4_FIXTURES = _SIDECAR / "brahmagyan" / "phala" / "l4_mitigation.py"
_MIGRATION = (
    _SIDECAR.parent / "supabase" / "migrations"
    / "582_f182_mantra_transliteration_citation_sweep.sql"
)


# ── The canonical bīja table, and how a served string is matched to it ───────

@pytest.fixture(scope="module")
def canon() -> dict[str, dict]:
    from brahmagyan.l0_remedy_corpus import PLANET_REMEDY_DATA
    return PLANET_REMEDY_DATA


@pytest.fixture(scope="module")
def rows() -> list[dict]:
    from brahmagyan.l0_remedy_corpus import build_all_remedies
    return build_all_remedies()


# A bīja of this class always ends `Sah <graha-name-in-dative> Namah`. The dative
# is what identifies WHICH graha the string claims to address — which is exactly
# how the wrong-graha defects (Saturn's row carrying Sun's bīja) are detectable.
_DATIVE_TO_PLANET = {
    "suryaya": "sun",
    "chandraya": "moon",
    "bhaumaya": "mars",
    "budhaya": "mercury",
    "gurave": "jupiter",
    "shukraya": "venus",
    "shanaischaraya": "saturn",
    "rahave": "rahu",
    "ketave": "ketu",
}

# `Om <syllables> Sah <dative> Namah`, tolerant of surrounding prose/quotes.
_BIJA_RE = re.compile(
    r"Om\s+[A-Za-z]+\s+[A-Za-z]+\s+[A-Za-z]+\s+Sah\s+([A-Za-z]+)\s+Namah",
    re.IGNORECASE,
)


def _bija_occurrences(text: str) -> list[tuple[str, str]]:
    """Yield (matched_string, planet) for every navagraha bīja in `text`."""
    found = []
    for m in _BIJA_RE.finditer(text or ""):
        planet = _DATIVE_TO_PLANET.get(m.group(1).lower())
        if planet is not None:
            found.append((m.group(0), planet))
    return found


def _scan_tree() -> list[tuple[str, str, str]]:
    """(source_label, matched_bija_string, planet) across every swept surface."""
    out: list[tuple[str, str, str]] = []

    from brahmagyan.l0_remedy_corpus import build_all_remedies
    for r in build_all_remedies():
        blob = " ".join(
            str(r.get(k) or "")
            for k in ("mantra_text", "mantra_transliteration", "prescription_text")
        )
        for s, p in _bija_occurrences(blob):
            out.append((f"l0_remedy_corpus:{r['remedy_id']}", s, p))

    for path in sorted(_CORPUS_YAML_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            continue
        for r in data:
            if not isinstance(r, dict):
                continue
            blob = " ".join(
                str(r.get(k) or "")
                for k in ("mantra_transliteration", "mantra_text", "remedy_text",
                          "prescription_text", "classical_attestation_text")
            )
            for s, p in _bija_occurrences(blob):
                out.append((f"{path.name}:{r.get('remedy_id')}", s, p))

    for path in (_L2_FIXTURES, _L4_FIXTURES):
        text = path.read_text(encoding="utf-8")
        # Source is a Python literal continued across lines; join so a bīja split
        # over an implicit string concatenation is still seen as one string.
        flat = re.sub(r'"\s*\n\s*"', "", text)
        for s, p in _bija_occurrences(flat):
            out.append((path.name, s, p))

    return out


# ── The canonical table must itself be coherent ─────────────────────────────

class TestCanonicalTable:
    def test_every_canonical_bija_matches_its_own_devanagari(self, canon):
        """`beej_iast` is a transliteration of `beej_sa`, computed not trusted."""
        checked = 0
        for planet, d in canon.items():
            sa, iast = d.get("beej_sa"), d.get("beej_iast")
            if not sa or not iast:
                continue
            derived = re.sub(r"\s+", " ", devanagari_to_iast(sa)).strip()
            assert derived == re.sub(r"\s+", " ", iast).strip(), (
                f"{planet}: beej_sa transliterates to {derived!r}, "
                f"but beej_iast says {iast!r}"
            )
            checked += 1
        assert checked == 9, f"expected all 9 grahas covered, covered {checked}"

    def test_canonical_ascii_beej_names_the_right_graha(self, canon):
        """The ASCII `beej` addresses the graha whose entry it sits in."""
        for planet, d in canon.items():
            occ = _bija_occurrences(d["beej"])
            assert len(occ) == 1, f"{planet}: {d['beej']!r} did not parse as one bīja"
            assert occ[0][1] == planet, (
                f"{planet}: canonical beej addresses {occ[0][1]}, not {planet}"
            )


# ── R-1 — every served bīja equals the canonical one for its own graha ───────

class TestBijaFidelity:
    def test_scan_actually_covers_the_corpus(self):
        """The detector must not pass by finding nothing (§N.8)."""
        found = _scan_tree()
        assert len(found) >= 40, (
            f"bīja scan found only {len(found)} occurrences — the extractor has "
            "stopped seeing the corpus, so a green result here means nothing"
        )
        sources = {s.split(":")[0] for s, _, _ in found}
        for expected in ("l0_remedy_corpus", "gemstones.yaml", "vrata.yaml",
                         "yantras.yaml", "tantric.yaml",
                         "l2_remediation_grounded.py", "l4_mitigation.py"):
            assert any(x.startswith(expected.split(".")[0]) for x in sources), (
                f"{expected} contributed no bīja occurrence to the scan"
            )

    def test_every_bija_in_the_tree_matches_its_grahas_canonical_form(self, canon):
        """
        Catches all three F-182 defect shapes at once:
          wrong graha  — 'Om Hraam Hreem Hraum Sah Shanaischaraya Namah'
          wrong word   — '... Sah Guruve Namah'   (dative of guru is gurave)
          wrong length — 'Om Bhram Bhreem Bhroum ...'  (भ्रां is bhraam)
        """
        bad = []
        for src, served, planet in _scan_tree():
            expected = canon[planet]["beej"]
            if served.strip().lower() != expected.strip().lower():
                bad.append(f"  {src}\n    served:   {served}\n    canonical: {expected}")
        assert not bad, (
            "bīja string(s) disagree with the corpus's own canonical table:\n"
            + "\n".join(bad)
        )

    def test_no_surface_still_carries_a_pre_fix_form(self):
        """Belt-and-braces literal sweep, including prose the regex may not span."""
        stale = ["Guruve Namah", "Bhram Bhreem Bhroum", "Sram Sreem Sraum",
                 "Shram Shreem Shroum", "Kram Kreem Kraum Sah Ketave",
                 "Hraam Hreem Hraum Sah Shanaischaraya", "Sah Shanaye Namah"]
        offenders = []
        targets = list(_CORPUS_YAML_DIR.glob("*.yaml")) + [
            _SIDECAR / "brahmagyan" / "l0_remedy_corpus.py", _L2_FIXTURES, _L4_FIXTURES,
        ]
        for path in targets:
            text = path.read_text(encoding="utf-8")
            for needle in stale:
                # A comment recording the historical correction is not a defect.
                for line in text.splitlines():
                    s = line.strip()
                    if needle in line and not s.startswith("#"):
                        offenders.append(f"{path.name}: {s[:110]}")
        assert not offenders, "stale mantra form(s) still present:\n" + "\n".join(offenders)


# ── R-2 — the bīja class no longer claims BPHS as its source ────────────────

class TestBijaAttribution:
    def test_no_bija_row_attributes_its_mantra_to_bphs(self, rows):
        offenders = []
        for r in rows:
            if not _bija_occurrences(str(r.get("mantra_text") or "")):
                continue
            ref = str(r.get("classical_ref") or "")
            cite = str(r.get("source_citation") or "")
            cid = str(r.get("source_canonical_id") or "")
            if cid == "BPHS" or ref.startswith("BPHS") or cite.startswith("BPHS"):
                offenders.append(
                    f"  {r['remedy_id']}: canonical_id={cid!r} ref={ref!r} cite={cite!r}"
                )
        assert not offenders, (
            "R-2: bīja-carrying row(s) still attribute the mantra to BPHS:\n"
            + "\n".join(offenders)
        )

    def test_bija_rows_cite_the_navagraha_tradition(self, rows):
        cited = [
            r for r in rows
            if _bija_occurrences(str(r.get("mantra_text") or ""))
        ]
        # 11 — the Ch.88 domain-scaffold cohort. The 9 `*_matrix_*` bīja rows are
        # NOT counted here: PR #1429 moved their transliteration to IAST, which
        # this ASCII extractor deliberately does not parse, and their citations
        # are already guarded by test_f23_mantra_script_and_citation.py.
        assert len(cited) >= 11, f"only {len(cited)} bīja rows found — scan too narrow"
        for r in cited:
            ref = str(r.get("classical_ref") or "")
            assert ref.startswith("Navagraha bīja tradition;"), (
                f"{r['remedy_id']}: classical_ref must lead with the actual "
                f"transmitting tradition, got {ref!r}"
            )
            if "BPHS" in ref:
                assert "upāya context only" in ref, (
                    f"{r['remedy_id']}: BPHS may appear only as labelled upāya "
                    f"context, got {ref!r}"
                )

    def test_nama_mantra_row_is_explicitly_carved_out(self, rows):
        """
        `jupiter_spirituality_puja_01` serves the short nāma-mantra, not a bīja.
        R-2 does not reach it and BPHS Ch.88 legitimately covers the Bṛhaspati
        pūjā upāya. Pinned so a later sweep cannot tidy it into the bīja cohort,
        and so the R-1 dative fix cannot be reverted with it.
        """
        row = next(r for r in rows if r["remedy_id"] == "jupiter_spirituality_puja_01")
        assert row["mantra_text"] == "Om Gurave Namah"
        assert row["source_canonical_id"] == "BPHS"
        assert not _bija_occurrences(row["mantra_text"])


# ── The migration and the Python source must not drift ──────────────────────

class TestMigrationAgreesWithSource:
    def test_migration_exists_and_names_every_reattributed_row(self, rows):
        assert _MIGRATION.exists(), f"missing migration {_MIGRATION.name}"
        sql = _MIGRATION.read_text(encoding="utf-8")
        reattributed = sorted(
            r["remedy_id"] for r in rows
            if _bija_occurrences(str(r.get("mantra_text") or ""))
            and str(r.get("source_canonical_id")) == "classical_tradition"
            and "Ch.88" in str(r.get("classical_ref") or "")
        )
        assert len(reattributed) == 11, (
            f"expected 11 Ch.88-cohort rows reattributed in Python, got "
            f"{len(reattributed)}: {reattributed}"
        )
        missing = [rid for rid in reattributed if rid not in sql]
        assert not missing, (
            "migration 582 does not carry these Python-side corrections to "
            f"already-seeded rows: {missing}"
        )

    def test_migration_preserves_the_nama_mantra_carve_out(self):
        sql = _MIGRATION.read_text(encoding="utf-8")
        # The carve-out row must be named in the verification block, and must NOT
        # appear inside the R-2 reattribution's IN (...) list.
        assert "jupiter_spirituality_puja_01" in sql
        r2_block = sql.split("-- ── R-2:")[1].split("-- ── Verification")[0]
        # Statement text only — the block's own comment explains the exclusion.
        r2 = "\n".join(
            ln for ln in r2_block.splitlines() if not ln.strip().startswith("--")
        )
        assert "jupiter_spirituality_puja_01" not in r2, (
            "the nāma-mantra row must not be inside the R-2 reattribution set"
        )
