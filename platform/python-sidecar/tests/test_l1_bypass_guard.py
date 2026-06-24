"""
test_l1_bypass_guard.py — Guard: no L1 writer may hard-code L0-owned classical facts.

Sealed 2026-06-24 as part of Foundation Integrity Campaign FIX 2.
Any redline failure here means an L0-bypass has been re-introduced; fix the writer, not the test.
"""
import re
from pathlib import Path

WRITERS_DIR = Path(__file__).parent.parent / "ga_writers"

GA_WRITER_FILES = [
    "ga_condition_writer.py",
    "ga_structural_writer.py",
    "ga_sensitive_writer.py",
    "ga_dashas_writer.py",
    "ga_yoga_writer.py",
]

# ── Forbidden patterns (L0 bypass signatures) ────────────────────────────────

# Old wrong Rahu/Ketu exaltation assignments (Gemini/Sagittarius are wrong per L0 seal)
_STALE_RAHU_EXALT   = re.compile(r'"Rahu"\s*:\s*"Gemini"')
_STALE_KETU_EXALT   = re.compile(r'"Ketu"\s*:\s*"Sagittarius"')
_STALE_RAHU_DEBIT   = re.compile(r'"Rahu"\s*:\s*"Sagittarius"')
_STALE_KETU_DEBIT   = re.compile(r'"Ketu"\s*:\s*"Gemini"')

# Inline vimshottari cycle definition (must read from reference_nakshatras)
_INLINE_NAK_CYCLE   = re.compile(r'_NAK_LORD_CYCLE\s*=\s*\[')
_INLINE_NAK_LORDS   = re.compile(r'^NAKSHATRA_LORDS_1BASED\s*=', re.MULTILINE)

# Inline sign lords dict (must read from reference_signs)
_INLINE_SIGN_LORDS  = re.compile(r'^SIGN_LORDS\s*=\s*\{', re.MULTILINE)

# Inline nakshatra lords list in sensitive writer
_INLINE_NAK_LORDS_S = re.compile(r'^NAK_LORDS\s*=\s*\[', re.MULTILINE)

# Mercury stale atichara threshold (was 2.5, sealed at 2.0)
_MERCURY_STALE_SAMA = re.compile(r'"Mercury".*sama_hi.*2\.5')


def _source(fname: str) -> str:
    return (WRITERS_DIR / fname).read_text(encoding="utf-8")


def test_no_stale_rahu_ketu_exaltation():
    """Rahu exaltation must be Taurus (not Gemini); Ketu must be Scorpio (not Sagittarius)."""
    for fname in GA_WRITER_FILES:
        src = _source(fname)
        assert not _STALE_RAHU_EXALT.search(src), f"{fname}: stale Rahu exaltation=Gemini"
        assert not _STALE_KETU_EXALT.search(src), f"{fname}: stale Ketu exaltation=Sagittarius"
        assert not _STALE_RAHU_DEBIT.search(src),  f"{fname}: stale Rahu debilitation=Sagittarius"
        assert not _STALE_KETU_DEBIT.search(src),  f"{fname}: stale Ketu debilitation=Gemini"


def test_no_inline_nakshatra_lord_cycle():
    """Nakshatra lord cycle must be read from reference_nakshatras, not defined inline."""
    for fname in ["ga_dashas_writer.py"]:
        src = _source(fname)
        assert not _INLINE_NAK_CYCLE.search(src), f"{fname}: inline _NAK_LORD_CYCLE definition found"
        assert not _INLINE_NAK_LORDS.search(src), f"{fname}: inline NAKSHATRA_LORDS_1BASED= found"


def test_no_inline_sign_lords():
    """Sign lords must be read from reference_signs, not defined inline."""
    src = _source("ga_sensitive_writer.py")
    assert not _INLINE_SIGN_LORDS.search(src), "ga_sensitive_writer.py: inline SIGN_LORDS= found"
    assert not _INLINE_NAK_LORDS_S.search(src), "ga_sensitive_writer.py: inline NAK_LORDS= found"


def test_no_stale_mercury_threshold():
    """Mercury atichara threshold sealed at 2.0 per L0 2026-06-24; 2.5 is wrong."""
    src = _source("ga_condition_writer.py")
    assert not _MERCURY_STALE_SAMA.search(src), \
        "ga_condition_writer.py: Mercury sama_hi=2.5 found — should be 2.0"
