"""Jaimini chara-karaka role vocabulary — single source for the L1 writers.

ga_sensitive OWNS the karaka derivation (``karaka_chara_position``); ga_vargas
READS ga_sensitive's kn_rao assignments and never re-derives them (CLAUDE.md
N.5 — L1 is the authority; N.7 item 3 — no wrapper-local constant may shadow an
L1-computed value). This module holds only the *vocabulary* both writers must
agree on: the school identifiers, the rank -> role-name lists, and the alias
fact_key. It holds no computed value.

Rulings (SS N-69, binding):
  * Headline school = ``kn_rao_rahu_included`` (8 grahas, Rahu reckoned by
    ``30 - (long % 30)``). ``parashari_rahu_excluded`` (7 grahas) stays the
    named variant.
  * 8-scheme role order (BPHS 32.13-17, sourced_ocr_unverified; J1 print-edition
    check pending) = Atma, Amatya, Bhratri, Matri, Pitri, Putra, Gnati, Dara.
  * 7-scheme role order is unchanged from before this lane: it carries no
    PITRIKARAKA subject. Source note: BPHS 32.13-17 (and the editor's note after
    it) records only that some authorities "consider Matrukaraka and
    Putrakaraka as identical" and so count seven karakas; it does not say the
    Matrikaraka doubles as Pitrikaraka, and it does not give a rank -> role
    table for the 7-scheme. The 7 labels above are this writer's pre-existing
    convention, retained by the SS ruling, not a transcription of that note
    (sourced_ocr_unverified; J1 print-edition check pending).
  * STRIKARAKA is a labelled ALIAS of the Darakaraka in the 8-scheme (same
    graha). It is emitted as an extra fact_key on the DARAKARAKA subject, never
    as a ninth subject row and never as a STRIKARAKA subject.
"""
from __future__ import annotations

from typing import Final

KARAKA_SCHOOL_PARASHARI: Final[str] = "parashari_rahu_excluded"
KARAKA_SCHOOL_KN_RAO: Final[str] = "kn_rao_rahu_included"

# Rank (1-based) -> chart_facts.fact_subject for karaka_chara_position.
KARAKA_ROLES_7: Final[tuple[str, ...]] = (
    "ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "MATRIKARAKA",
    "PUTRAKARAKA", "GNATIKARAKA", "DARAKARAKA",
)
KARAKA_ROLES_8: Final[tuple[str, ...]] = (
    "ATMAKARAKA", "AMATYAKARAKA", "BHRATRIKARAKA", "MATRIKARAKA",
    "PITRIKARAKA", "PUTRAKARAKA", "GNATIKARAKA", "DARAKARAKA",
)

KARAKA_ROLES_BY_SCHOOL: Final[dict[str, tuple[str, ...]]] = {
    KARAKA_SCHOOL_PARASHARI: KARAKA_ROLES_7,
    KARAKA_SCHOOL_KN_RAO: KARAKA_ROLES_8,
}

# STRIKARAKA alias (kn_rao school only): extra fact_key on the DARAKARAKA subject.
KARAKA_ALIAS_SUBJECT: Final[str] = "DARAKARAKA"
KARAKA_ALIAS_FACT_KEY: Final[str] = "strikaraka_alias"
KARAKA_ALIAS_LABEL: Final[str] = "STRIKARAKA"

# Short abbreviations used by ga_vargas (karaka_per_varga subjects), rank order
# of the 8-scheme.
KARAKA_ABBREVIATIONS_8: Final[tuple[str, ...]] = (
    "AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK",
)
