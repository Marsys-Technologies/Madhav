"""
services/ka_kota_chakra/logic.py — pure, DB-free computation for item 16
(Kota-Chakra, the fort chakra). SHAD_DARSHANA_BRIEF_v2_0.md §1 item 16:
"transiting grahas mapped to the kota's stambha/madhya/prakara/bahya rings
relative to the janma nakshatra, with entry/exit and the attack/defence
reading." Wave W3. Registered as writer id `ka_kota_chakra` (layer kala).

── WHAT KOTA-CHAKRA IS ───────────────────────────────────────────────────────
A muhūrta/nimitta technique that treats the native's 27-nakshatra cycle
(counted forward from the janma/birth nakshatra) as a fort (kota) with four
concentric rings — Stambha (the innermost pillar/heart), Durgantara a.k.a.
Madhya (the inner-middle ward), Prākāra (the boundary wall), and Bāhya (the
exterior) — and reads a transiting graha's classical nature (benefic/malefic)
against which ring it currently occupies as an "attack vs. defence" signal.

── RING TABLE — NOW A VERSIONED L0 ASSET (ADJUDICATION-9, 2026-08-01) ────────
The Kota-Chakra ring partition (which nakshatra-counts-from-janma fall in
Stambha/Durgantara/Prakara/Bahya) previously lived as an inline dict in this
module. ANTARYĀMIN's ADJUDICATION-9
(00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md) ruled that the DATA-HONESTY RAIL's
three conjuncts — "cited, versioned L0 row" — require the partition to live
in `bg_kota_chakra_rings` (see `brahmagyan.l0_kota_chakra_rings` for the full
disclosure: citation tier, row-count note, versioning), not as writer-code.
**No served value changed** — this module no longer HOLDS the ring
assignment, it only computes WITH one handed to it. `ring_for_count()` below
now takes the ring-position partition as a parameter (`ring_sets`), sourced
by `services/ka_kota_chakra/writer.py` from the L0 table at run time via
`brahmagyan.l0_kota_chakra_rings.ring_sets_by_name()` semantics (read from
the DB, not the Python module, in production — the module is the seed/write
path and the shared byte-identity reference for tests).

For the counting convention and the full tier-(iii) citation disclosure, see
`brahmagyan/l0_kota_chakra_rings.py`'s own module docstring — it is now the
canonical source, not a restatement here (duplicate-copy rail).

── WHAT IS PURE ARITHMETIC (no citation needed) ──────────────────────────────
`count_from_janma`, `ring_for_count`, `detect_ring_runs`, `run_containing_date`
are deterministic arithmetic over already-established facts (a graha's
sidereal nakshatra index, the janma nakshatra index, and — for
`ring_for_count` — a ring-position partition handed in by the caller) — not
classical doctrine themselves, so B.10 does not apply to them the way it
applies to the ring table.

── ATTACK/DEFENCE READING ─────────────────────────────────────────────────────
`attack_defence_reading` combines the (cited, tier-iii) ring assignment with
the classical natural benefic/malefic classification (matches the
codebase's own repeated convention — see ga_sensitive_degree_writer.py,
ga_yoga_writer.py, ga_structural_writer.py's identical NATURAL_MALEFICS/
NATURAL_BENEFICS sets) into a deterministic, template-driven posture/severity
label. This combination (ring x nature -> label) is THIS writer's OWN
synthesis, not an independently-cited classical rule — the writer marks it
`uncited_extension=True` at the row level, exactly like ka_gochara_resonance's
documented distinction between cited primitives and synthesized linkages
(services/ka_gochara_resonance/writer.py's own docstring).
"""
from __future__ import annotations

from datetime import date
from typing import TypedDict

# ── Ring NAMES (pure vocabulary — not the partition data; see module
# docstring) ───────────────────────────────────────────────────────────────

ALL_RING_NAMES: tuple[str, str, str, str] = ("stambha", "durgantara", "prakara", "bahya")


def ring_for_count(count: int, ring_sets: dict[str, frozenset[int]]) -> str:
    """count is 1..27 (1-indexed distance from janma nakshatra, inclusive of
    the janma nakshatra itself as count=1). Raises ValueError outside 1..27.

    ring_sets: {ring_name: frozenset(ring_position)} — the ring-position
    partition, now sourced from the bg_kota_chakra_rings L0 table
    (ADJUDICATION-9), not a module constant here. Callers: writer.py builds
    this from a DB read; tests build it from
    brahmagyan.l0_kota_chakra_rings.ring_sets_by_name() (or the byte-identity
    fixture, for the pre-move golden comparison)."""
    if not (1 <= count <= 27):
        raise ValueError(f"count_from_janma out of range: {count} (expected 1..27)")
    for ring_name, members in ring_sets.items():
        if count in members:
            return ring_name
    raise AssertionError(f"count {count} not in any ring — partition invariant violated")


def count_from_janma(nak_idx_0based: int, janma_nak_idx_0based: int) -> int:
    """1-indexed nakshatra count from janma (0-based nakshatra indices in,
    e.g. from services.ka_graha_sancara.engine.NAKSHATRAS ordering)."""
    return ((nak_idx_0based - janma_nak_idx_0based) % 27) + 1


# ── Natural benefic/malefic classification (matches the codebase's own
# repeated convention — see module docstring) ────────────────────────────────

NATURAL_MALEFICS: frozenset[str] = frozenset({"Sun", "Mars", "Saturn", "Rahu", "Ketu"})
NATURAL_BENEFICS: frozenset[str] = frozenset({"Moon", "Mercury", "Jupiter", "Venus"})


class AttackDefenceReading(TypedDict):
    posture: str
    severity: str
    is_natural_malefic: bool


# ring -> (malefic posture, malefic severity, benefic posture, benefic severity)
_READING_TABLE: dict[str, tuple[str, str, str, str]] = {
    "bahya": ("attacking", "watch", "reinforcing_perimeter", "supportive"),
    "prakara": ("breaching_the_wall", "elevated", "guarding_the_wall", "supportive"),
    "durgantara": ("inside_the_middle_ward", "high", "settled_in_the_middle_ward", "supportive"),
    "stambha": ("at_the_heart", "acute", "anchoring_the_heart", "strong_support"),
}


def attack_defence_reading(graha: str, ring: str) -> AttackDefenceReading:
    """Deterministic, template-driven combination of ring + classical nature.
    THIS WRITER'S OWN SYNTHESIS (uncited_extension=True at the row level) —
    see module docstring."""
    if ring not in _READING_TABLE:
        raise ValueError(f"unknown ring {ring!r}; expected one of {ALL_RING_NAMES}")
    is_malefic = graha in NATURAL_MALEFICS
    malefic_posture, malefic_severity, benefic_posture, benefic_severity = _READING_TABLE[ring]
    if is_malefic:
        return {"posture": malefic_posture, "severity": malefic_severity, "is_natural_malefic": True}
    return {"posture": benefic_posture, "severity": benefic_severity, "is_natural_malefic": False}


# ── Contiguous-run (entry/exit) detection over a bounded scanned horizon ─────

class RingRun(TypedDict):
    nakshatra_idx: int
    start_date: date
    end_date: date
    start_truncated: bool
    end_truncated: bool


def detect_ring_runs(
    daily_nak_idx: list[tuple[date, int]],
    *,
    horizon_start: date,
    horizon_end: date,
) -> list[RingRun]:
    """Groups a sorted, contiguous daily (date, nakshatra_idx) series into
    maximal same-nakshatra runs. A run's start/end is marked `truncated` when
    it touches the edge of the SCANNED horizon — i.e. we genuinely do not know
    whether the graha entered/left earlier/later than what we scanned. This is
    the B.10/§N.7-item-6 honesty discipline: an honest truncation flag beats a
    precise-looking date we did not actually verify.

    `daily_nak_idx` must be sorted ascending by date with no gaps (the caller
    is responsible for supplying a complete daily series over
    [horizon_start, horizon_end]).
    """
    if not daily_nak_idx:
        return []

    runs: list[RingRun] = []
    run_start_date, run_nak_idx = daily_nak_idx[0]
    prev_date = run_start_date

    def _flush(end_date: date) -> None:
        runs.append({
            "nakshatra_idx": run_nak_idx,
            "start_date": run_start_date,
            "end_date": end_date,
            "start_truncated": run_start_date == horizon_start,
            "end_truncated": end_date == horizon_end,
        })

    for d, nak_idx in daily_nak_idx[1:]:
        if nak_idx != run_nak_idx:
            _flush(prev_date)
            run_start_date, run_nak_idx = d, nak_idx
        prev_date = d

    _flush(prev_date)
    return runs


def run_containing_date(runs: list[RingRun], as_of: date) -> RingRun | None:
    for r in runs:
        if r["start_date"] <= as_of <= r["end_date"]:
            return r
    return None
