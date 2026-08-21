"""
brahmagyan/dignity_oracle.py — B-01 Dignity Oracle

Single shared dignity classifier for all consumers that need sign-level
dignity classification with degree-gated moolatrikona support.

Data source: brahmagyan.l0_dignity_reference.DIGNITY_REFERENCE — the single,
dependency-free L0 reference (PAR-R-6, LEDGER_PRATINIDHI.md
par/pratinidhi-ledger: extraction to a shared brahmagyan/l0_* module does not
touch the FROZEN WriterBase contract, and matches the established sibling
convention — l0_class_priors, l0_class_lifetime_counts, l0_dasha_systems,
l0_doshas, l0_formula_constants, l0_ephemeris all already work this way).
`pipeline/orchestrator/writers/bg_dignity_reference.py` (the L0 writer that
seeds the DB table) imports the SAME module — one Python source, not two.

Returns one of: "exalted" | "debilitated" | "moolatrikona" | "own" | "neutral"
All lowercase — matching the live SQL vocabulary in chart_facts.fact_value_text.

Priority order (classical BPHS):
  1. exalted          — planet in its exaltation sign
  2. debilitated      — planet in its debilitation sign
  3. nodes early-exit — Rahu/Ketu: only exalted/debilitated/neutral (§2.1)
  4. moolatrikona     — in MT sign AND degree within [moolatrikona_from, moolatrikona_to)
  5. own              — in own sign (but not in MT range)
  6. neutral          — none of the above

B-01 lane spec: exaltation and debilitation are checked BEFORE moolatrikona;
moolatrikona is checked BEFORE own; degree gate is [from, to) half-open interval.
Jupiter at 0°-10° Sag = MT; at 15° Sag = own. Sun at 0°-20° Leo = MT; at 25° = own.

Nodes (Rahu/Ketu) carry ONLY exalted/debilitated/neutral — §2.1 neutral-default.

KNOWN GAP (flagged, not yet ruled on — see lanes/F-62/SPEC.md §7b): for Moon and
Mercury, the exaltation sign coincides with the moolatrikona sign (Taurus, Virgo
respectively), and this priority order checks exaltation by SIGN ONLY (no degree
gate) before moolatrikona — so "moolatrikona" is currently unreachable for these
two grahas at any degree. `l0_dignity_reference.DIGNITY_REFERENCE` already
carries an `exaltation_degree` field this classifier does not yet consult;
whether exaltation should itself be degree-gated is a classical-doctrine
question of the same shape as PAR-R-2, reserved for a future PRATINIDHI ruling.
"""
from __future__ import annotations

from brahmagyan.l0_dignity_reference import DIGNITY_REFERENCE as _DIGNITY_REFERENCE

# ── Static dignity data — derived from the shared L0 reference ────────────────
# Keyed by graha name (Title-case canonical form).
# "mt_sign": None means no moolatrikona tier for that graha.
# "mt_from" / "mt_to": the [from, to) degree range within the MT sign.
# "own": list of own sign names.

_DATA: dict[str, dict] = {
    row["graha"]: {
        "exaltation": row["exaltation_sign"],
        "debilitation": row["debilitation_sign"],
        "mt_sign": row["moolatrikona_sign"],
        "mt_from": row["moolatrikona_from"],
        "mt_to": row["moolatrikona_to"],
        "own": frozenset(row["own_signs"]),
    }
    for row in _DIGNITY_REFERENCE
}

_NODES: frozenset[str] = frozenset(["Rahu", "Ketu"])

# ── Emittable vocabulary (F-62) ───────────────────────────────────────────────
# The EXHAUSTIVE set of values `classify_dignity` can return, and therefore the
# exhaustive set of values that can appear in
# `chart_facts.graha_dignity_per_varga` / `fact_key='dignity_state'`.
#
# This constant exists because F-62 found the failure mode it prevents: when the
# B-01 oracle first became able to emit "moolatrikona", four downstream consumer
# maps could not spell it — three of them keyed on "mooltrikona" (no 'a'), one
# enumerated only a four-value scale — so a moolatrikona graha silently scored
# BELOW the plain "own" it used to score, in the exact tier classical Sthana Bala
# ranks HIGHEST after exaltation. Every consumer that maps a dignity_state to a
# score, tier, or valence must cover this set; `tests/test_f62_moolatrikona_
# downstream_vocabulary.py` is the detector that fails when one does not
# (CLAUDE.md §N.8 — a signal with no detector behind it is not a signal).
#
# Adding a tier here without updating that test's consumer roster will fail CI.
DIGNITY_STATES: frozenset[str] = frozenset(
    ["exalted", "debilitated", "moolatrikona", "own", "neutral"]
)

# Historic misspelling seen in pre-F-62 consumer maps. Kept ONLY so that legacy
# lookups against those maps do not silently regress to a default; nothing in
# this module emits it, and no new code should key on it.
LEGACY_MOOLATRIKONA_ALIASES: frozenset[str] = frozenset(["mooltrikona", "mulatrikona"])


def classify_dignity(graha: str, sign_name: str, degree_in_sign: float) -> str:
    """Classify the dignity of `graha` occupying `sign_name` at `degree_in_sign`.

    Parameters
    ----------
    graha : str
        Title-case canonical graha name (e.g. "Jupiter", "Rahu").
    sign_name : str
        Title-case sign name (e.g. "Sagittarius", "Taurus").
    degree_in_sign : float
        Degree within the sign, in the range [0.0, 30.0).
        Used for the moolatrikona degree gate only.

    Returns
    -------
    str
        One of: "exalted" | "debilitated" | "moolatrikona" | "own" | "neutral"
        (all lowercase, matching the live SQL vocabulary).

    Raises
    ------
    KeyError
        If `graha` is not in the 9-planet canonical set.
    """
    r = _DATA.get(graha)
    if r is None:
        raise KeyError(
            f"dignity_oracle: unknown graha {graha!r}. "
            f"Valid names: {sorted(_DATA)}"
        )

    # 1. Exaltation (highest priority — checked before MT)
    if sign_name == r["exaltation"]:
        return "exalted"

    # 2. Debilitation
    if sign_name == r["debilitation"]:
        return "debilitated"

    # 3. Nodes early-exit — no MT or own tier
    if graha in _NODES:
        return "neutral"

    # 4. Moolatrikona — degree-gated: [mt_from, mt_to)
    if (
        r["mt_sign"] is not None
        and sign_name == r["mt_sign"]
        and r["mt_from"] <= degree_in_sign < r["mt_to"]
    ):
        return "moolatrikona"

    # 5. Own sign (after MT check — MT wins when in range)
    if sign_name in r["own"]:
        return "own"

    # 6. Neutral
    return "neutral"
