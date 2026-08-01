"""
services/ka_sudarshana_varsha/logic.py — pure, DB-free computation for item 17
(Sudarśana-Chakra year-wheel). SHAD_DARSHANA_BRIEF_v2_0.md §1 item 17:
"the year-wheel triple-lagna progression technique." Wave W3. Registered as
writer id `ka_sudarshana_varsha` (layer kala) per the campaign's BINDING
naming ruling.

── NAMING RULING — CONFIRMED NAMESAKE-ONLY COLLISION (do not revisit) ────────
`bo_sudarshana.py` (L2 Bodha, `bodha_msr_signals` table) computes, per graha
and per ayanamsha, a STATIC house-position from three simultaneous reference
frames (Lagna, Chandra, Sūrya) AT BUILD TIME — a single number per graha, no
time axis. `ka_sudarshana_varsha` (this writer) does something categorically
different: it PROGRESSES all three reference points (JL/CL/SL) FORWARD through
the zodiac, one sign per year of the native's life, and stores the resulting
"active sign" for every reference point for every year of a full lifespan —
a genuinely temporal technique (L3 Kāla), unrelated in computation to L2's
static tri-frame house count. Same classical term ("Sudarśana Chakra"),
different layer, different computation — hence the distinct writer id.

── THE TECHNIQUE ─────────────────────────────────────────────────────────────
Per Maharishi Parashara's tri-lagna framework (Janma Lagna, Chandra Lagna =
natal Moon sign, Sūrya Lagna = natal Sun sign): each "varsha year" (year N of
life, 1-indexed, N=1 covering birth -> first birthday) advances EACH of the
three reference signs forward by (N-1) signs, cycling every 12 years — i.e.
"house 1 governs ages 1, 13, 25, ...; house 2 governs ages 2, 14, 26, ...".
This is the ROTATING YEAR-WHEEL scope of the technique. The fuller classical
"Sudarshana Chakra Dasha" also layers a 10-year primary + yearly secondary
sub-period structure on top of this wheel — THAT sub-dasha structure is
explicitly OUT OF SCOPE for this writer (a materially larger, separate
technique); this writer delivers the year-wheel progression only, which is
exactly what SHAD_DARSHANA_BRIEF_v2_0.md item 17 names. Extending to the full
sub-dasha structure is a natural, additive follow-on, not a defect of this
build.

`varsha_year_for_date`/`varsha_window` are plain calendar arithmetic off
`ctx.config['birth_params']` (the FROZEN-contract-provided input) — not an
L1-authoritative fact restatement, so §N.5 does not apply to them the way it
applies to natal sign facts (JL/CL/SL natal signs ARE read from L1
`chart_facts`, never recomputed — see writer.py).

`varsha_window` uses a simple N-1/N calendar-year-anniversary window (day-
grade, matches this campaign's day-grade-first discipline — CLAUDE.md /
SHAD_DARSHANA_BRIEF_v2_0.md §4: "No wave may be designed to REQUIRE sub-day
precision"), NOT a true tropical/anomalistic solar-return instant (which
would require an ephemeris root-find, W2G-class precision this writer does
not need or claim).
"""
from __future__ import annotations

from datetime import date
from typing import TypedDict

from dateutil.relativedelta import relativedelta

# Full-life horizon, matching the classical technique's designed scope and
# this codebase's own full-life-arc convention (e.g. ka_jivana_parva).
DEFAULT_MAX_VARSHA_YEAR = 120


def varsha_year_for_date(birth_date: date, as_of: date) -> int:
    """1-indexed 'year of life' N: N=1 covers [birth, first birthday), N=2
    covers [first birthday, second birthday), etc. `as_of` must be >= birth_date."""
    if as_of < birth_date:
        raise ValueError(f"as_of ({as_of}) precedes birth_date ({birth_date})")
    completed_birthdays = relativedelta(as_of, birth_date).years
    return completed_birthdays + 1


def active_house_offset(varsha_year: int) -> int:
    """0-based sign offset (0..11) to progress forward from a reference's own
    natal sign for the given varsha year."""
    if varsha_year < 1:
        raise ValueError(f"varsha_year must be >= 1, got {varsha_year}")
    return (varsha_year - 1) % 12


def progressed_sign_index(natal_sign_idx_0based: int, varsha_year: int) -> int:
    """0-based sign index (0=Aries..11=Pisces) the reference point occupies
    during the given varsha year."""
    return (natal_sign_idx_0based + active_house_offset(varsha_year)) % 12


def varsha_window(birth_date: date, varsha_year: int) -> tuple[date, date]:
    """Calendar [start, end) for this varsha year — day-grade N-1/N
    anniversary window (see module docstring for why this is not a true
    solar-return instant)."""
    if varsha_year < 1:
        raise ValueError(f"varsha_year must be >= 1, got {varsha_year}")
    start = birth_date + relativedelta(years=varsha_year - 1)
    end = birth_date + relativedelta(years=varsha_year)
    return start, end


class TriLagnaYear(TypedDict):
    jl_active_sign_idx: int
    cl_active_sign_idx: int
    sl_active_sign_idx: int
    tri_lagna_convergence: bool


def compute_tri_lagna_year(
    varsha_year: int,
    jl_natal_sign_idx: int,
    cl_natal_sign_idx: int,
    sl_natal_sign_idx: int,
) -> TriLagnaYear:
    """Progress all three reference points for one varsha year and flag
    tri-lagna convergence (all three active signs coincide) — a classically
    notable alignment year."""
    jl = progressed_sign_index(jl_natal_sign_idx, varsha_year)
    cl = progressed_sign_index(cl_natal_sign_idx, varsha_year)
    sl = progressed_sign_index(sl_natal_sign_idx, varsha_year)
    return {
        "jl_active_sign_idx": jl,
        "cl_active_sign_idx": cl,
        "sl_active_sign_idx": sl,
        "tri_lagna_convergence": jl == cl == sl,
    }
