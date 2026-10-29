"""Rule Book scorer - constants fixed by the locked yardstick (v1.0 as amended by v1.1).

Nothing here is tuned. Each value cites the clause that fixes it. The scorer source hash
(``source_sha256``) is part of every result, so a later edit cannot pass unnoticed.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

SCORER_VERSION = "rulebook-scorer-v1.0"
YARDSTICK_V10_SHA256 = "6e2dc5f3e42f0a357c2f15fae7210427bbab2c37182d69c3774974b4d9a34591"
YARDSTICK_V11_SHA256 = "8071d944dfa858d4d1e7d6b226589d8ef0eb470cc3faa3eaa3cd9e8a6ad4efbd"
CLUSTER_TABLE_SHA256 = "b3e0a6b9f31e41dbd974f667c3507af6d2681b180ba78b694d6aeccddf79499f"  # SUR-RB-23

# ── planes / families (v1.1 B4: F-N dropped, m <= 2) ────────────────────────
FAMILY_DASHA = "dasha"
FAMILY_TRANSIT = "transit"
FAMILIES = (FAMILY_DASHA, FAMILY_TRANSIT)

# ── directions and polarity (v1.0 section 0) ────────────────────────────────
FAVOURABLE = "favourable"
UNFAVOURABLE = "unfavourable"
POLARITY_OF_DIRECTION = {FAVOURABLE: "promotive", UNFAVOURABLE: "obstructive"}
OPPOSITE_DIRECTION = {FAVOURABLE: UNFAVOURABLE, UNFAVOURABLE: FAVOURABLE}
GENERAL = "GENERAL"

# ── windows (v1.1 C1: G1 = day +-1, G2 = calendar month; no G3, no R in this sample) ─
G1 = "G1"
G2 = "G2"
G1_WINDOW_DAYS = 3
WINDOW_CLASS_OF_GRADE = {G1: "3d", G2: "month"}  # v1.1 D8 window classes
MOON_BODY = "chandra"  # v1.1 C1: a member whose transiting body is the Moon is scored on G1 only
MIN_ASSESSED_SHARE = 0.5  # v1.0 section 0: a window with fewer than half its days assessed is not scored

# ── blocks (v1.1 D1) ───────────────────────────────────────────────────────
BLOCK_DAYS_5Y = 1826
BLOCK_DAYS_15Y = 5479
MERGE_BELOW_5Y = 913  # a final block under this merges into the previous one (v1.0 4.1)
MERGE_BELOW_15Y = BLOCK_DAYS_15Y // 2  # AMBIGUITY (flagged): v1.1 D1 gives no merge threshold for the 15y scheme; half a block, as 913 is half of 1826

SCHEMES: Dict[str, Tuple[Tuple[str, int, int], ...]] = {
    # family -> ((scheme name, block days, merge-below days), ...); the first scheme is the primary one
    FAMILY_DASHA: (("5y", BLOCK_DAYS_5Y, MERGE_BELOW_5Y), ("15y", BLOCK_DAYS_15Y, MERGE_BELOW_15Y)),
    FAMILY_TRANSIT: (("5y", BLOCK_DAYS_5Y, MERGE_BELOW_5Y),),
}

# ── statistics (v1.1 D2) ───────────────────────────────────────────────────
Z25_MIN_UNIT_EPISODES = 10
Z25_TOP_FRACTION = 0.25  # the mean of the top quartile of unit z-scores; k = ceil(0.25 * n_units), at least 1

# ── draws (v1.1 D1, D3, D4) ────────────────────────────────────────────────
DRAWS_PRODUCTION = 100_000
DRAW_CHUNK = 4_000  # draws are generated in chunks of this size (memory); part of the definition of the random stream
MIN_DRAWS_CALIBRATION = 2_000  # v1.1 F2: at least 2,000 draws per check in the calibration
MIN_ELIGIBLE_DONORS = 5  # v1.1 D3

# ── footprint gate and testability (v1.0 4.4 as changed by v1.1 D7, D8) ─────
TOUCH_RATE_GATE = 0.60
TESTABLE_MIN_EPISODES = 250
TESTABLE_MIN_CHARTS = 15
TESTABLE_MIN_UNIT_SHARE = 0.5

# ── outcomes (v1.1 Part E) ─────────────────────────────────────────────────
ALPHA_STRONG = 0.05
ALPHA_MIDDLE = 0.10
MIN_CHARTS_FOR_VERDICT = 20
MIN_DASHA_EPISODES_FOR_VERDICT = 400  # v1.0 section 1, v1.1 A7

# ── extraction noise (v1.1 A8) ─────────────────────────────────────────────
EXTRACTION_NOISE = 0.67

# ── F2 gate (v1.1 F2) ──────────────────────────────────────────────────────
GATE_PER_FAMILY = 0.02
GATE_OVERALL = 0.03
GATE_MIN_STUDIES = 5_000
GATE_SANITY_Q = 0.30
GATE_SANITY_POWER = 0.80


@dataclass(frozen=True)
class ScoreConfig:
    """Run parameters that do not change the statistics' definitions."""

    draws: int = DRAWS_PRODUCTION
    seed: int = 20261030
    fallback_primary_set: bool = False  # v1.1 A7: all-occurrence set is primary -> direction-consistency check


SOURCE_FILES = (
    "__init__.py",
    "config.py",
    "model.py",
    "core.py",
    "outcome.py",
    "footprint.py",
    "runner.py",
)


def source_sha256() -> str:
    """sha256 over the scorer's source files (names and bytes, in a fixed order)."""
    h = hashlib.sha256()
    here = Path(__file__).resolve().parent
    for name in SOURCE_FILES:
        p = here / name
        h.update(name.encode("utf-8") + b"\0")
        h.update(p.read_bytes() if p.exists() else b"<missing>")
        h.update(b"\0")
    return h.hexdigest()
