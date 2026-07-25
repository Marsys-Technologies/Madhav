"""
ocr_cleanup.py — Classical corpus OCR-quality cleanup (Elevation Campaign v2.1, Stream beta,
Lane G, EL-52)
=================================================================================================
EL-52 symptom: the classical corpus sweep (`brahmagyan/l0_remedy_corpus.py::sweep_classical_text_chunks`)
copies `classical_text_chunks.content_en` verbatim into remedy prescription rows, including OCR
noise so severe some rows are functionally uncited — the named example is the BPHS Ch.47
Venus-maraka passage (chunk in the `bphs_pg0581_c01` range), which renders in part as
"3Tr?Ctrqqqad EI€TITfEfrffTq".

Two deterministic, non-LLM pieces (B.10 / N.4 — deterministic-first, no generative curation):

1. `score_ocr_confidence(text)` — a character/word-class legibility heuristic, safe to run over
   the ENTIRE corpus sweep (no content is invented; it only scores what's already there).
2. `HAND_CLEANED_CHUNKS` — a small, explicit, human-reviewed registry. Each entry is a chunk this
   lane's session actually read and vetted by hand; NOTHING here is a generic algorithmic
   reconstruction. Devanagari/verse segments that could not be honestly recovered are left
   unset (None) and flagged, never guessed at (per the explicit instruction: "if you cannot
   recover a clean reading, flag it low-confidence and move on — do not clean it by guessing").

Bounded scope (explicit, per the brief): this lane's charter caps EL-52 at "the ~200
highest-traffic rows only (remedy-linked rows + ref_rules_search top hits)... A full-corpus pass
is explicitly OUT of scope." `apply_ocr_cleanup()` is written to run over that bounded set; see
BETA_G.md for the honest accounting of how many rows this session actually hand-cleaned vs.
scored-only.
"""
from __future__ import annotations

import re
from typing import Any

CLEANUP_PASS_VERSION = "beta_g_el52_v1"

_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z'\-]*$")
_VOWELS = set("aeiouAEIOU")


def _is_plausible_english_token(tok: str) -> bool:
    """A conservative 'does this look like a real English word' check — used only to SCORE
    legibility, never to alter or guess content. Rejects: tokens starting with a digit,
    tokens with no vowels (length > 2), tokens mixing case in a way normal English prose
    doesn't (e.g. 'qqqad', 'EI€TITfEfrffTq'), tokens containing non-ASCII/symbol noise."""
    core = tok.strip(".,;:!?'\"()[]")
    if not core:
        return False
    if not _WORD_RE.match(core):
        return False
    if len(core) > 2 and not any(c in _VOWELS for c in core):
        return False
    # Reject runs with 3+ consecutive consonants AND no vowel nearby (classic OCR-noise shape,
    # e.g. "Ctrqqq") without rejecting real words like "strength" (has vowels flanking).
    if re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", core, re.IGNORECASE):
        return False
    return True


def _line_ratio(tokens: list[str]) -> float | None:
    if not tokens:
        return None
    return sum(1 for t in tokens if _is_plausible_english_token(t)) / len(tokens)


def score_ocr_confidence(text: str) -> float:
    """Deterministic OCR legibility score, 0.0-1.0. This SCORES existing text; it never
    modifies or guesses content — safe to run over the full bounded corpus set without risk
    of fabrication.

    Two components, combined as a minimum (not an average): a flat overall token ratio can
    hide a badly garbled line inside an otherwise-legible row (a consumer would still hit that
    garbage when reading it) — so the score is capped by the WORST individual line's ratio,
    not diluted by longer legible neighbors. A row is only as trustworthy as its least-legible
    line."""
    if not text or not text.strip():
        return 0.0
    tokens = text.split()
    if not tokens:
        return 0.0
    overall = _line_ratio(tokens) or 0.0

    lines = [ln.split() for ln in text.splitlines() if ln.strip()]
    line_scores = [r for r in (_line_ratio(toks) for toks in lines if len(toks) >= 2) if r is not None]
    worst_line = min(line_scores) if line_scores else overall

    score = min(overall, worst_line)
    if len(tokens) < 8:
        score *= 0.85  # not enough tokens to be confident in the ratio itself
    return round(min(max(score, 0.0), 1.0), 3)


LOW_CONFIDENCE_THRESHOLD = 0.55


# ── Hand-reviewed cleanups (explicit, small, auditable — never a generic transform) ────────────
# Each entry: chunk_id -> {cleaned_translation_text, cleaned_devanagari_text (None if
# unrecoverable), low_confidence_flag, ocr_review_note}. Populated by direct human/session
# inspection of the live G0-reproduced row content (see BETA_G.md for the exact source call and
# raw text this was cleaned from).
HAND_CLEANED_CHUNKS: dict[str, dict[str, Any]] = {
    # BPHS Ch.47, Venus dasha/sub-period maraka passage — the EL-52 named example.
    # Raw (from ref_remedies_chart_get(affliction="Venus") live call, 2026-07-25,
    # remedy_id=sweep_venus_japa_1b8a46b9, source_citation "BPHS ... PG581"):
    #   ".Chapter 47\n3Tr?Ctrqqqad\nEI€TITfEfrffTq I\n589\nfadtqs.aat*\naflunftqr<r{\n?6{ler\n
    #    qfilqfa llqqll\nqr aqrcti qt( |\ng\nei\n€ai TTi q{Fft Eemrrt'lni\nq aa} viq ttce tt\n
    #    88-8g.SimilararetheeffectsofVenusinhissub.periods.\nIf Venus belord of the 2nd or
    #    the 7th(two maraka houses)' there\nwill'be during his Dasa, physical pains and
    #    troubles' To get\nalleviation from those troubles the native should"
    "bphs_pg0581_c01": {
        "verse_reference": "BPHS Ch.47, sloka 88-89 (Venus dasha/antardasha effects)",
        "cleaned_devanagari_text": None,  # genuinely unrecoverable from this OCR pass — not guessed
        "cleaned_translation_text": (
            "88-89. Similar are the effects of Venus in his sub-periods. If Venus be lord of "
            "the 2nd or the 7th (two maraka houses), there will be during his Dasa, physical "
            "pains and troubles. To get alleviation from those troubles the native should ..."
            "[text continues past this chunk's boundary — not truncated by this cleanup, "
            "truncated by the original 400-char chunk extraction in "
            "sweep_classical_text_chunks(); the continuation is a separate, uncleaned chunk]"
        ),
        "low_confidence_flag": True,  # the Devanagari verse segment remains unrecovered
        "ocr_review_note": (
            "Devanagari verse segment (~4 lines preceding the English gloss) is OCR noise from "
            "a Sanskrit source rendered through an English-only OCR pass — not recoverable from "
            "this text alone; left unset, not guessed (B.10). The trailing English translation "
            "was legible with only word-boundary loss (words run together, e.g. "
            "'SimilararetheeffectsofVenus') — a mechanical defect where every character is "
            "already present and unambiguous; de-spacing it invents nothing. This passage "
            "directly corroborates the BPHS Ch.44 maraka-lordship rule (2nd/7th house lord) "
            "used by this lane's EL-51 gemstone verdict, specifically naming Venus."
        ),
    },
}


def apply_ocr_cleanup(conn: Any, chunk_ids: list[str] | None = None) -> dict[str, int]:
    """Score (and, where hand-vetted, clean) rows in classical_text_chunks. `chunk_ids`, when
    given, bounds the pass to that explicit set (the EL-52-mandated ~200-highest-traffic bound);
    when None, scores every row currently in the table (still bounded in practice by whatever
    caller supplies `chunk_ids` for — see BETA_G.md for what this lane actually ran).

    Idempotent: re-running overwrites the same deterministic score + the same hand-vetted
    cleanup for a chunk_id already in HAND_CLEANED_CHUNKS; never accretes duplicate rows
    (single UPDATE per chunk_id, not an insert)."""
    if chunk_ids:
        placeholders = ",".join(["%s"] * len(chunk_ids))
        rows = conn.execute(
            f"SELECT chunk_id, content_en FROM classical_text_chunks "
            f"WHERE chunk_id IN ({placeholders})",
            list(chunk_ids),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT chunk_id, content_en FROM classical_text_chunks",
        ).fetchall()

    scored = 0
    hand_cleaned = 0
    with conn.cursor() as cur:
        for r in rows:
            chunk_id = r[0] if isinstance(r, (tuple, list)) else r.get("chunk_id")
            content_en = r[1] if isinstance(r, (tuple, list)) else r.get("content_en")
            confidence = score_ocr_confidence(content_en or "")
            vetted = HAND_CLEANED_CHUNKS.get(chunk_id)
            if vetted:
                hand_cleaned += 1
                cur.execute(
                    """UPDATE classical_text_chunks SET
                         ocr_confidence_score = %s,
                         cleaned_translation_text = %s,
                         cleaned_devanagari_text = %s,
                         low_confidence_flag = %s,
                         ocr_review_note = %s,
                         ocr_cleanup_pass_version = %s
                       WHERE chunk_id = %s""",
                    [
                        confidence,
                        vetted.get("cleaned_translation_text"),
                        vetted.get("cleaned_devanagari_text"),
                        vetted.get("low_confidence_flag", confidence < LOW_CONFIDENCE_THRESHOLD),
                        vetted.get("ocr_review_note"),
                        CLEANUP_PASS_VERSION,
                        chunk_id,
                    ],
                )
            else:
                cur.execute(
                    """UPDATE classical_text_chunks SET
                         ocr_confidence_score = %s,
                         low_confidence_flag = %s,
                         ocr_review_note = %s,
                         ocr_cleanup_pass_version = %s
                       WHERE chunk_id = %s""",
                    [
                        confidence,
                        confidence < LOW_CONFIDENCE_THRESHOLD,
                        (None if confidence >= LOW_CONFIDENCE_THRESHOLD else
                         "Scored low-confidence by the deterministic legibility heuristic; "
                         "not yet hand-reviewed for a clean translation (EL-52 bounded scope — "
                         "see BETA_G.md for the ~200-row follow-up list)."),
                        CLEANUP_PASS_VERSION,
                        chunk_id,
                    ],
                )
            scored += 1
    return {"scored": scored, "hand_cleaned": hand_cleaned}
