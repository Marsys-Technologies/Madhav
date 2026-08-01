"""
services/ka_vedha_gochara/logic.py — pure, DB-free computation for item 5
(Vedha application + Sarvatobhadra chakra grid — closes defect R-19).
SHAD_DARSHANA_BRIEF_v2_0.md §1 item 5: "Vedha application + REAL
Sarvatobhadra grid (closes R-19)." Wave W3. Registered as writer id
`ka_vedha_gochara` (layer kala).

── WHAT VEDHA IS (two DISTINCT classical mechanisms, both served here) ───────
This writer computes TWO separately-cited vedha (obstruction) mechanisms,
distinguished by the row-level `vedha_kind` column — never flattened into one
undifferentiated list (§N.6):

1. `house_vedha` — the coarser, HOUSE-level Gochara vedha (BPHS Ch.29;
   Phaladeepika Ch.26; `bg_transit_rules` rule_type='vedha', migration 266,
   REAL and populated). Classical Gochara doctrine: a graha transiting a
   classically FAVOURABLE house counted FROM THE NATAL MOON has its good
   result CANCELLED if another transiting graha simultaneously occupies the
   paired "vedha house" (also counted from the natal Moon). This exact
   cancellation semantics — "vedha cancels the primary transit's effect only
   when both houses are simultaneously occupied" — already has a working,
   tested implementation in this codebase:
   `services/gochara_grammar/primitives.py::gochara_vedha_pair`, invoked
   per-domain-configuration by `kala_trigger`. This writer does NOT re-derive
   or duplicate that engine (§N.5-adjacent discipline — one classical rule,
   one interpretation); it is a DIFFERENT, simpler, standalone per-chart
   SERVING surface: rather than being triggered by a specific
   `ResonanceTarget`/event-class configuration, it scans EVERY graha's own
   sign-occupancy history against `bg_transit_rules` directly and reports
   vedha status for the chart's currently-relevant transits, independent of
   any domain query. This is the genuinely NEW capability item 5 asks for —
   "vedha application... applied to currently-active transits" — that did
   not exist as a standalone, queryable, per-chart artifact before this
   writer (only as an internal primitive fired by specific domain triggers).

2. `sarvatobhadra` — the finer-grained, NAKSHATRA-level Sarvatobhadra Chakra
   vedha (Prasna Marga; Muhurta Chintamani / Jyotish Sara Sangraha per the
   `l1_sarvatobhadra_positions`/`l1_sarvatobhadra_vedha` table comments,
   migration `_archive/140_sarvatobhadra_chakra.sql`). THIS IS THE R-19 ITEM.

── R-19 — HONEST DISCLOSURE (read before assuming "real grid" means a
populated 9×9 grid table) ───────────────────────────────────────────────────
R-19, as recorded in KALA_TRANSFORMATION_HANDOFF_v1_0.md §II.3, is: "the
Sarvatobhadra vedha grid has zero rows (honest approximation flagged
uncited_extension) — W3's vedha work forces the real grid." This writer
DOES force the real grid question, and here is exactly what was and was not
found:

  - `l1_sarvatobhadra_positions` (28 nakshatra grid cells) and
    `l1_sarvatobhadra_vedha` (14 vedha pairs) — the tables migration 140
    created for exactly this purpose — are CONFIRMED still empty (checked
    this session): no INSERT statements exist in that migration or its
    follow-on (`_archive/144_vedha_extended.sql`), and no other file in this
    repository populates them.
  - The ingested classical-text corpus (`00_ARCHITECTURE/SOURCE_DATA/
    classical_texts/`) was checked this session: it holds BPHS, Jaimini
    Sutram, KP, and KP_Reader material only — NO Muhurta Chintamani or
    Jyotish Sara Sangraha text, the two sources migration 140's own table
    comments cite for the SBC grid. Tier (i) (ingested-corpus citation) is
    therefore UNAVAILABLE for this specific table, confirmed by direct
    search, not assumed.
  - Unlike `ka_kota_chakra`'s ring table (which had a single, internally
    consistent tier-(iii) secondary description this session could transcribe
    with a checkable partition invariant — see that writer's own docstring),
    the Sarvatobhadra Chakra's specific 9×9 grid layout (which nakshatra
    occupies which row/column, and therefore which 14 pairs are truly
    diametrically opposite in the GRID's geometry, as opposed to merely
    opposite in the 27-nakshatra CYCLE) is not a single settled fact this
    session could responsibly transcribe from memory: multiple regional
    Jyotish traditions present the SBC's starting cell and traversal
    direction differently, and fabricating ONE specific grid_row/grid_col
    assignment — or a specific 14-pair list dressed up as "the" classical
    table — without a citable primary or secondary source in hand would be
    exactly the invented-precision failure the DATA-HONESTY RAIL and B.10
    exist to prevent (LAW ZERO: "honest-empty beats fabricated-full").
  - DECISION (this session, disclosed for native/Verifier adjudication):
    `l1_sarvatobhadra_positions`/`l1_sarvatobhadra_vedha` are NOT populated
    by this PR. What this PR DOES do — the genuine, honest progress on
    R-19 — is take the EXISTING, already-disclosed algorithmic approximation
    (`services/gochara_grammar/sarvatobhadra.py::opposite_nakshatra_id`,
    which computes the vedha nakshatra as the nearest-integer 180°-opposition
    point in the 27-nakshatra CYCLE — an approximation of the SBC's grid
    relationship, not a reproduction of its actual geometry, exactly as that
    module's own extensive docstring already discloses) and, for the FIRST
    TIME, wires it into a live, served, per-chart computation — previously
    this function existed only as an internal primitive invoked by specific
    `kala_trigger` domain configurations, never as a standalone queryable
    per-chart artifact. Every row this writer produces under
    `vedha_kind='sarvatobhadra'` carries `uncited_extension=True` and the
    SAME disclosure sarvatobhadra.py already established — this is R-19's
    "zero rows, uncited approximation" state becoming "a real, live,
    per-chart SERVED uncited approximation with the exact same honesty
    grade" — real forward progress, but NOT "the real classical grid" R-19's
    headline names. The grid-population gap is filed as an
    ADJUDICATION-PENDING corpus-ingestion item, exactly mirroring
    `ka_kota_chakra`'s own precedent for its ring table (see that writer's
    module docstring for the identical disclosure pattern) — should
    `l1_sarvatobhadra_vedha` ever be populated with a native-approved,
    source-verified table, `_vedha_pairs_from_db` in sarvatobhadra.py (this
    writer's own DB-sourced lookup path, reused unchanged) becomes the
    primary path automatically, with zero code change to this writer.

── HOUSE-VEDHA REFERENCE POINT (Moon, not Lagna) ─────────────────────────────
`bg_transit_rules.primary_house`/`vedha_house` are documented in
`brahmagyan/l0_transit.py` (§2) as "house FROM MOON" — the standard classical
Gochara convention (BPHS Ch.29 reads transits primarily from the natal Moon,
Chandra Rāśi). This writer's house arithmetic uses the natal MOON's sign as
the reference point, matching `bg_transit_rules`'s own documented convention
exactly — never the natal Lagna (a different, equally classical, but
DIFFERENT reference the codebase's own dual-reference gochara (item 8)
already keeps separate).

── SCOPE (disclosed, not an oversight) ───────────────────────────────────────
`house_vedha` rows are emitted ONLY for (graha, house) combinations that
`bg_transit_rules` documents as `rule_type='favourable'` WITH a non-null
`vedha_house` — i.e. exactly the classically vedha-checkable cases. Rows for
`rule_type='unfavourable'` primary houses (which the table itself carries
`vedha_house=NULL` for — classically, a bad transit has no vedha to check)
and houses with no rule at all are out of scope for THIS writer (item 5 is
specifically "vedha application", not a restatement of all Gochara
favourable/unfavourable phala, which `ka_gochara_sweep` already serves).
"""
from __future__ import annotations

from datetime import date
from typing import Optional, TypedDict

HOUSE_VEDHA = "house_vedha"
SARVATOBHADRA = "sarvatobhadra"
VEDHA_KINDS: tuple[str, ...] = (HOUSE_VEDHA, SARVATOBHADRA)


class SignRun(TypedDict):
    sign_idx: int
    start_date: date
    end_date: date
    start_truncated: bool
    end_truncated: bool


def detect_sign_runs(
    daily_sign_idx: list[tuple[date, int]],
    *,
    horizon_start: date,
    horizon_end: date,
) -> list[SignRun]:
    """Groups a sorted, contiguous daily (date, sign_idx) series into maximal
    same-sign runs. Identical algorithm to
    `ka_moorti_nirnaya.logic.detect_sign_runs` / `ka_kota_chakra.logic.
    detect_ring_runs` — duplicated per this campaign's established
    one-writer-per-module convention (see ka_kota_chakra/ka_sudarshana_varsha
    precedent), not shared, so this writer stays independently reviewable."""
    if not daily_sign_idx:
        return []

    runs: list[SignRun] = []
    run_start_date, run_sign_idx = daily_sign_idx[0]
    prev_date = run_start_date

    def _flush(end_date: date) -> None:
        runs.append({
            "sign_idx": run_sign_idx,
            "start_date": run_start_date,
            "end_date": end_date,
            "start_truncated": run_start_date == horizon_start,
            "end_truncated": end_date == horizon_end,
        })

    for d, sign_idx in daily_sign_idx[1:]:
        if sign_idx != run_sign_idx:
            _flush(prev_date)
            run_start_date, run_sign_idx = d, sign_idx
        prev_date = d

    _flush(prev_date)
    return runs


def house_from_moon(sign_idx: int, moon_sign_idx: int) -> int:
    """1-indexed house number counted from the natal Moon's sign (Chandra
    Rāśi) — the reference point `bg_transit_rules` itself documents. House 1
    = the graha is transiting the natal Moon's own sign."""
    return ((sign_idx - moon_sign_idx) % 12) + 1


def sign_from_house(moon_sign_idx: int, house_num: int) -> int:
    """Inverse of house_from_moon: the 0-based sign index for a given house
    number counted from the natal Moon's sign."""
    return (moon_sign_idx + house_num - 1) % 12


class Overlap(TypedDict):
    start: date
    end: date


def overlap_window(
    a_start: date, a_end: date, b_start: date, b_end: date,
) -> Optional[Overlap]:
    """The overlapping [start, end] sub-window of two closed date intervals,
    or None if they do not overlap. Used to determine whether an obstructing
    graha's occupancy of the vedha house/nakshatra genuinely coincides with
    the primary transit's own window — classical vedha cancellation requires
    SIMULTANEOUS occupancy, not merely occupancy at some point in the whole
    scanned horizon."""
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if start > end:
        return None
    return {"start": start, "end": end}


__all__ = [
    "HOUSE_VEDHA",
    "SARVATOBHADRA",
    "VEDHA_KINDS",
    "SignRun",
    "detect_sign_runs",
    "house_from_moon",
    "sign_from_house",
    "Overlap",
    "overlap_window",
]
