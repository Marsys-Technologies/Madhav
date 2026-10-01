"""canonical_formulas.py -- the ONE declaration of which ``formula_id`` is canonical for each
multi-formula ``chart_facts`` category (Python mirror).

Why this exists (INVESTIGATION_L1_DUPLICATE_KEYS_v1_0.md, PR #2861; SS decision 2026-10-01):
``ga_sensitive`` deliberately writes every classical variant of seven categories as separate rows,
one per ``formula_id`` (WP-1.8). ``formula_id`` is already part of the table's unique key, so the
460 "duplicated" natural keys per chart are legitimate named variants, not defects. The defect was
on the READ side: readers that picked one row per (subject, key) without pinning the formula served
a physical-order-dependent winner. This table is what a reader pins to.

MIRROR + PARITY. The TS mirror is
``platform/src/lib/retrieval/registry/layers/L1_ganita/canonical_formulas.ts``. This module is a
SIBLING of ``verification_vocab.py`` / ``l0_reference.py`` on purpose: those are frozen L0 digests
and are never edited for a constant. ``tests/test_canonical_formulas_parity.py`` (and the vitest
twin next to the TS file) read BOTH files and assert equality, including every variants list.

STATUS: every canonical choice is (R) PROVISIONAL until J1 (the acharya review) and is on the J1
reviewers' list by name. ``esoteric_point_mrityu`` has NO canonical formula by design: all three
reckonings are served with ``formula_id`` disclosed and no headline value; a reader that needs a
single value returns an honest null with reason ``no_canonical_formula``.

Stdlib only and import-free of the rest of the package, so the governance lint
(``platform/scripts/governance/check_fact_category_pinning.py``) can load it by file path.

NOT touched by this module: writers. ``ga_sensitive`` keeps emitting every variant; nothing here
collapses, deletes or re-keys a row.
"""
from __future__ import annotations

NO_CANONICAL_FORMULA_REASON = "no_canonical_formula"

CANONICAL_FORMULA_STATUS = "provisional_until_J1"

# category -> {"canonical": formula_id | None, "variants": [formula_id, ...]}
# When canonical is set, variants EXCLUDES it; when canonical is None, variants lists every formula.
CANONICAL_FORMULAS = {
    "karaka_chara_position": {"canonical": "kn_rao_rahu_included", "variants": ["parashari_rahu_excluded"]},
    "esoteric_point_yogi": {"canonical": "bphs_93_20", "variants": ["alt_96_40"]},
    "esoteric_point_avayogi": {"canonical": "bphs_93_20", "variants": ["alt_96_40"]},
    "esoteric_point_brahma": {"canonical": "kn_rao_rahu_included", "variants": ["parashari_rahu_excluded"]},
    "esoteric_point_shiva": {"canonical": "kn_rao_rahu_included", "variants": ["parashari_rahu_excluded"]},
    "esoteric_point_vishnu": {"canonical": "kn_rao_rahu_included", "variants": ["parashari_rahu_excluded"]},
    "esoteric_point_mrityu": {"canonical": None, "variants": ["bphs_ch39", "saravali", "tajik_aapamrityu"]},
}

# The Jaimini chara-karaka school the L1 build already pins (ga_structural karaka-web, section N.5).
CANONICAL_KARAKA_SCHOOL = CANONICAL_FORMULAS["karaka_chara_position"]["canonical"]


def multi_formula_categories():
    """Declared categories, in table order."""
    return list(CANONICAL_FORMULAS)


def is_multi_formula_category(category):
    return category in CANONICAL_FORMULAS


def canonical_formula_of(category):
    """Canonical formula for a category; None for an undeclared OR a no-canonical category."""
    spec = CANONICAL_FORMULAS.get(category)
    return spec["canonical"] if spec else None


def all_formulas_of(category):
    """Every formula a declared category can serve: canonical first (if any), then variants."""
    spec = CANONICAL_FORMULAS.get(category)
    if not spec:
        return []
    head = [spec["canonical"]] if spec["canonical"] else []
    return head + list(spec["variants"])
