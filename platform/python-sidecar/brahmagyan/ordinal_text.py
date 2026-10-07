"""English ordinal formatting for generated narration (pure, deterministic, no I/O).

One shared helper for every writer that turns a house / offset / count into a sentence
("2nd from Sun", "11th house"). Hard-coding a 'th' suffix prints '1th', '2th', '3th', '21th'
and so on; this function is the single place the English rule lives.

Rule: 11, 12, 13 (and any number ending in 11/12/13, e.g. 111) take 'th'; otherwise a last
digit of 1/2/3 takes 'st'/'nd'/'rd'; everything else takes 'th'.

Strict on type: a non-int (float, str, None, bool) raises TypeError rather than printing a
plausible-looking but invented ordinal (CLAUDE.md §N.7 item 6: an honest failure beats an
invented judgment).
"""
from __future__ import annotations


def ordinal(n: int) -> str:
    """Return ``n`` with its English ordinal suffix: 1 -> '1st', 2 -> '2nd', 11 -> '11th', 22 -> '22nd'."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise TypeError(f"ordinal() needs an int, got {type(n).__name__}: {n!r}")
    m = abs(n)
    if 11 <= m % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(m % 10, "th")
    return f"{n}{suffix}"
