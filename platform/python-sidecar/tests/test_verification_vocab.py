"""
test_verification_vocab.py — SAMĀPTI · B-VERIFSTATUS-VOCAB · DVA Ruling 13.

Guards the three sides of the one defect that A7-N8-AUDIT surfaced as F-11/F-25/F-38:

  1. `ga_nakshatra.py` must never again stamp an unconditional PASS. Its
     `verification_pass_status` now comes from a detector that CAN return a different
     answer — proven here by feeding it a chart whose attribution disagrees with its
     own longitude and watching the status go `divergent_flagged`.
  2. No writer in the sidecar may emit `pass` / `PASS`, or any literal outside the
     settled vocabulary.
  3. The Python vocabulary and the TypeScript vocabulary in
     `platform/src/lib/retrieval/envelope.ts` must agree, member for member and
     verified-flag for verified-flag.
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_REPO = _SIDECAR.parent.parent
sys.path.insert(0, str(_SIDECAR))

from ga_writers.verification_vocab import (  # noqa: E402
    ALL_STATUSES,
    PROHIBITED_STATUSES,
    RESTRICTED_TABLE_VOCAB,
    UNVERIFIED_DEFAULT,
    VERIFIED_STATUSES,
    VERIFICATION_PASS_STATUS_VOCAB,
    assert_legal,
    canonical,
    is_verified,
)

_ENVELOPE_TS = _REPO / "platform" / "src" / "lib" / "retrieval" / "envelope.ts"


# ── 1. the vocabulary itself ──────────────────────────────────────────────────


def test_verified_set_is_exactly_two_pass_verified():
    """§N.8: only a status backed by a detector that could have disagreed is verified.

    If a later lane promotes another member (e.g. `classical_match`) it must do the
    per-site earnedness audit first and change this assertion deliberately — the point
    is that widening the verified set can never happen by accident.
    """
    assert VERIFIED_STATUSES == frozenset({"two_pass_verified"})


def test_pass_spellings_are_prohibited_not_merely_absent():
    assert PROHIBITED_STATUSES == frozenset({"pass", "PASS"})
    for bad in PROHIBITED_STATUSES:
        assert bad not in ALL_STATUSES
        assert not is_verified(bad)
        with pytest.raises(ValueError, match="PROHIBITED"):
            assert_legal(bad)


def test_is_verified_is_case_sensitive():
    """Case-folding here is exactly how 5,428 unverified rows nearly became grounded."""
    assert is_verified("two_pass_verified")
    assert not is_verified("TWO_PASS_VERIFIED")
    assert not is_verified("Two_Pass_Verified")
    assert not is_verified(None)


def test_restricted_table_vocab_is_a_subset_of_the_settled_vocabulary():
    """The live CHECK on chart_dashas / chart_divisionals must not allow anything the
    settled vocabulary does not know about."""
    assert RESTRICTED_TABLE_VOCAB <= ALL_STATUSES


def test_restricted_tables_reject_out_of_constraint_statuses_before_insert():
    assert_legal("single", table="chart_dashas")
    with pytest.raises(ValueError, match="CHECK constraint"):
        assert_legal("documented_approximation", table="chart_divisionals")


def test_deprecated_alias_resolves():
    assert canonical("single_pass") == "single"
    assert canonical("single") == "single"
    assert canonical("two_pass_verified") == "two_pass_verified"


def test_unverified_default_is_legal_and_unverified():
    assert UNVERIFIED_DEFAULT in ALL_STATUSES
    assert not is_verified(UNVERIFIED_DEFAULT)


# ── 2. the ga_nakshatra detector (F-11) ───────────────────────────────────────


def _chart_output(longitude_deg: float, nakshatra_id: int, pada: int) -> dict:
    return {
        "grahas": [{
            "name": "Moon",
            "longitude_deg": longitude_deg,
            "nakshatra_id": nakshatra_id,
            "pada": pada,
        }],
        "ascendant": {},
    }


def _rows_for_moon() -> list[dict]:
    common = {
        "chart_id": "test-chart", "ayanamsha_id": "lahiri_chitrapaksha",
        "build_id": "test-build", "fact_subject": "MOON",
    }
    return [
        {**common, "fact_category": "graha_nakshatra_join", "fact_key": "nakshatra_id_ref",
         "fact_value_num": 25.0},
        {**common, "fact_category": "graha_pada_join", "fact_key": "pada_number_ref",
         "fact_value_num": 3.0},
        {**common, "fact_category": "graha_nakshatra_join", "fact_key": "gana",
         "fact_value_text": "Manushya"},
        {**common, "fact_category": "graha_tara_bala", "fact_key": "tara_number",
         "fact_value_num": 5.0},
    ]


def _statuses(chart_output: dict) -> dict[tuple[str, str], str]:
    from pipeline.orchestrator.writers.ga_nakshatra import (
        _enrich_rows, _nakshatra_pada_verdicts,
    )
    verdicts = _nakshatra_pada_verdicts(chart_output)
    enriched = _enrich_rows(_rows_for_moon(), "test-engine", "2026-07-30T00:00:00Z", verdicts)
    return {(r["fact_category"], r["fact_key"]): r["verification_pass_status"] for r in enriched}


def test_ga_nakshatra_never_emits_a_pass_literal():
    src = (_SIDECAR / "pipeline" / "orchestrator" / "writers" / "ga_nakshatra.py").read_text()
    assert '"verification_pass_status":  "PASS"' not in src
    assert not re.search(r'''["']verification_pass_status["']\s*:\s*["']pass["']''', src, re.I)


def test_agreeing_attribution_earns_two_pass_verified():
    # Purva Bhadrapada (nakshatra 25) spans 320°00'–333°20'; 326.0° is pada 2.
    got = _statuses(_chart_output(326.0, 25, 2))
    assert got[("graha_nakshatra_join", "nakshatra_id_ref")] == "two_pass_verified"
    assert got[("graha_pada_join", "pada_number_ref")] == "two_pass_verified"


def test_non_attribution_rows_are_never_promoted_by_the_detector():
    """The detector checks the nakshatra/pada attribution and NOTHING else. A
    reference-table relay (gana) and a tara-bala step count are not things it verified,
    so they stay honest even on a fully-agreeing chart (§N.8)."""
    got = _statuses(_chart_output(326.0, 25, 2))
    assert got[("graha_nakshatra_join", "gana")] == UNVERIFIED_DEFAULT
    assert got[("graha_tara_bala", "tara_number")] == UNVERIFIED_DEFAULT
    assert not is_verified(got[("graha_nakshatra_join", "gana")])


def test_CAN_FAIL_disagreeing_attribution_goes_divergent_not_verified():
    """THE can-fail proof. Same rows, same code path — only the engine's attribution is
    made inconsistent with its own longitude. A rubber-stamp cannot produce this."""
    # 326.0° is genuinely nakshatra 25 pada 2; claim 14 / 1 instead.
    got = _statuses(_chart_output(326.0, 14, 1))
    assert got[("graha_nakshatra_join", "nakshatra_id_ref")] == "divergent_flagged"
    assert got[("graha_pada_join", "pada_number_ref")] == "divergent_flagged"
    assert not is_verified(got[("graha_nakshatra_join", "nakshatra_id_ref")])


def test_missing_longitude_cannot_be_verified():
    """No second pass possible → honest `single`, never a green."""
    from pipeline.orchestrator.writers.ga_nakshatra import _nakshatra_pada_verdicts
    verdicts = _nakshatra_pada_verdicts({
        "grahas": [{"name": "Moon", "nakshatra_id": 25, "pada": 2}], "ascendant": {},
    })
    assert verdicts["MOON"] == {"nakshatra": UNVERIFIED_DEFAULT, "pada": UNVERIFIED_DEFAULT}


@pytest.mark.parametrize("lon,nak,pada", [
    (0.0, 1, 1),          # Ashwini pada 1, lower boundary
    (13.3333332, 1, 4),   # last instant of Ashwini
    (13.3333334, 2, 1),   # first instant of Bharani
    (359.9999, 27, 4),    # Revati pada 4, upper boundary
])
def test_independent_derivation_matches_classical_boundaries(lon, nak, pada):
    from pipeline.orchestrator.writers.ga_nakshatra import _derive_nakshatra_pada
    assert _derive_nakshatra_pada(lon) == (nak, pada)


# ── 3. estate-wide: no writer emits an illegal literal (F-25) ─────────────────

_LITERAL_RE = re.compile(r'''["']verification_pass_status["']\s*:\s*["']([A-Za-z_]+)["']''')


def _writer_sources() -> list[pathlib.Path]:
    out = []
    for p in sorted(_SIDECAR.rglob("*.py")):
        rel = p.relative_to(_SIDECAR).as_posix()
        if rel.startswith("tests/") or "__tests__" in rel or rel.startswith("ga_writers/verification_vocab"):
            continue
        out.append(p)
    return out


def test_no_writer_emits_a_prohibited_or_unknown_status():
    offenders: list[str] = []
    for p in _writer_sources():
        for i, line in enumerate(p.read_text().splitlines(), 1):
            m = _LITERAL_RE.search(line)
            if m and m.group(1) not in ALL_STATUSES:
                offenders.append(f"{p.relative_to(_SIDECAR).as_posix()}:{i} -> {m.group(1)!r}")
    assert not offenders, (
        "writer(s) emit a verification_pass_status outside the settled vocabulary "
        f"{sorted(ALL_STATUSES)}:\n  " + "\n  ".join(offenders)
    )


# ── 4. build ⇄ serve parity (F-38) ────────────────────────────────────────────

_TS_ENTRY_RE = re.compile(
    r"\{\s*status:\s*'([a-z_0-9]+)'\s*,\s*verified:\s*(true|false)\b", re.M,
)


def _ts_vocab() -> dict[str, bool]:
    text = _ENVELOPE_TS.read_text()
    start = text.index("VERIFICATION_PASS_STATUS_VOCAB")
    end = text.index("] as const", start)
    return {m.group(1): m.group(2) == "true" for m in _TS_ENTRY_RE.finditer(text[start:end])}


def test_python_and_typescript_vocabularies_are_identical():
    ts = _ts_vocab()
    py = {e.status: e.verified for e in VERIFICATION_PASS_STATUS_VOCAB}
    assert ts, f"could not parse the vocabulary out of {_ENVELOPE_TS}"
    assert ts == py, (
        "build-side and serve-side verification vocabularies have drifted.\n"
        f"  only in python: {sorted(set(py) - set(ts))}\n"
        f"  only in ts:     {sorted(set(ts) - set(py))}\n"
        f"  verified-flag mismatch: "
        f"{sorted(k for k in set(py) & set(ts) if py[k] != ts[k])}"
    )


def _strip_ts_comments(text: str) -> str:
    """Drop // line comments and /* */ blocks so an assertion about CODE is not
    satisfied or defeated by prose. (The envelope's comments deliberately quote the
    old predicate verbatim to explain what was removed.)"""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in text.splitlines())


def test_typescript_union_type_matches_the_table_and_python():
    """`VerificationPassStatus` is what makes the TS table self-checking (tsc rejects a
    table member missing from the union). It must also match Python, or the union — a
    type other modules import — becomes a fifth definition again."""
    text = _ENVELOPE_TS.read_text()
    start = text.index("export type VerificationPassStatus")
    body = text[start:text.index("export interface VerificationVocabEntry", start)]
    union = set(re.findall(r"\|\s*'([a-z_0-9]+)'", body))
    py = {e.status for e in VERIFICATION_PASS_STATUS_VOCAB}
    assert union == py, (
        f"union-vs-table drift: only in union {sorted(union - py)}, "
        f"only in table {sorted(py - union)}"
    )
    assert not (union & PROHIBITED_STATUSES)


def test_typescript_grounding_predicate_is_derived_not_hand_written():
    """The serve-layer grounding check must call the shared predicate. An inline
    `s === 'two_pass_verified' || s === 'pass'` is the exact hand-maintained literal
    pair that Ruling 13 exists to delete."""
    code = _strip_ts_comments(_ENVELOPE_TS.read_text())
    assert "isVerifiedPassStatus(r['verification_pass_status'])" in code
    # No executable line may compare the field against a status literal directly.
    assert not re.search(r"verification_pass_status'?\]?\s*===", code)
    assert "=== 'pass'" not in code
    # And the banned spellings must not appear as vocabulary members anywhere.
    assert not re.search(r"status:\s*'(pass|PASS)'", code)
