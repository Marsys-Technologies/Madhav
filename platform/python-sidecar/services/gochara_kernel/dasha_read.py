"""The §4.0 daśā read contract, as ONE implementation (GOCHARA_DESIGN_SPECS_v1_4
§4.0 [L]; ASTRA v1.1 P1-2 / v1.2 P1-1).

Every daśā operand the Gochara family reads from `public.chart_dashas` is pinned
to chart, ayanāṃśa, system, verification tier and ONE build — an unpinned read
is a defect (v1.2 B38-F1). Two consumers read under this contract: the step06a
class-context document (scripts/kala_gochara_cutover, which delegates here) and
the registered '5.0' writer's `period_running_at` prerequisite evaluation. They
share this module so the rule cannot drift between them (§N.7 item 3: a second
copy of the pin logic is a wrapper-local rule that can shadow the first).

The pin is NEVER a constant in this module: the canonical chart is pinned by the
frozen contract (`services.gochara_rules.permission.DASHA_READ_CONTRACT`, read,
never copied); every other chart pins to the single tier-filtered build it
carries; several builds, a NULL build, or a canonical-chart build that is not the
frozen one is a CONFLICT — raised, never resolved by row order.
"""
from __future__ import annotations

from typing import Callable

from services.gochara_grammar import dasha_data as DD

PINNED_SYSTEM = "vimshottari"
#: the period LEVEL tokens a P1 anchor carries → the chart_dashas `level_n` (§4.0: 1 MD, 2 AD, 3 PD)
LEVEL_N = {"md": 1, "ad": 2, "pd": 3}


def select_dasha_read_contract(chart_id: str, dasha_periods: list[dict]) -> dict:
    """The §4.0 pin Vimśottarī rows are read under: the frozen contract's build
    for the canonical chart when present; else the single build the
    tier-filtered rows carry; several builds ⇒ a conflict — refuse (raise),
    never row-order pick; no Vimśottarī rows ⇒ build None (disclosed)."""
    from services.gochara_rules.permission import DASHA_READ_CONTRACT
    vim = [p for p in dasha_periods if p.get("system_id") == PINNED_SYSTEM]
    null_build = sum(1 for p in vim if p.get("build_id") is None)
    builds = sorted({str(p.get("build_id")) for p in vim if p.get("build_id") is not None})
    pinned = DASHA_READ_CONTRACT["build_id"]
    if str(chart_id) == DASHA_READ_CONTRACT["chart_id"]:
        # the canonical chart is PINNED by the frozen contract: any other
        # sole build is a wrong build, never accepted (ASTRA v1.1 P1-2)
        if pinned not in builds:
            raise DD.DashaReadConflict(
                f"chart_dashas §4.0: the frozen read contract pins build {pinned} "
                f"for chart {chart_id}, but the two_pass_verified vimshottari rows "
                f"carry {builds or 'no build'} — refusing an unpinned read")
        build = pinned
        basis = "GOCHARA_DESIGN_SPECS_v1_4 §4.0 pinned build"
    elif null_build:
        raise DD.DashaReadConflict(
            f"chart_dashas §4.0: {null_build} two_pass_verified vimshottari rows "
            f"for chart {chart_id} carry a NULL build_id — unpinnable, refusing")
    elif len(builds) == 1:
        build = builds[0]
        basis = "single two_pass_verified build present"
    elif not builds:
        build = None
        basis = "no vimshottari rows at the read tier"
    else:
        raise DD.DashaReadConflict(
            f"chart_dashas §4.0: several two_pass_verified vimshottari builds "
            f"{builds} for chart {chart_id} — an unpinned read is a defect; "
            "refusing to pick by row order")
    return {"system_id": PINNED_SYSTEM, "build_id": build,
            "tier": DD.READ_CONTRACT_TIER,
            "ayanamsha_id": DASHA_READ_CONTRACT["ayanamsha_id"],
            "basis": basis, "builds_seen": builds}


def load_pinned_vimshottari(conn, chart_id: str) -> tuple[list[dict], dict]:
    """(1) a RAW, non-canonicalized read of the tier-pinned Vimśottarī rows
    selects the build pin; (2) the rows are then fetched PINNED to that build and
    canonicalized — a foreign build's overlapping rows never enter the
    duplicate/conflict pass. Returns (rows, contract); rows is [] when the chart
    has none at the read tier (honest empty — the caller reports 'unknown')."""
    raw = DD.fetch_dasha_periods_multilevel(
        conn, chart_id, systems=[PINNED_SYSTEM], canonicalize=False)
    contract = select_dasha_read_contract(chart_id, raw)
    contract["raw_vimshottari_rows"] = len(raw)
    if contract["build_id"] is None:
        return [], contract
    rows = DD.fetch_dasha_periods_multilevel(
        conn, chart_id, systems=[PINNED_SYSTEM], build_id=contract["build_id"])
    contract["rows_excluded_by_build_pin"] = len(raw) - len(
        [r for r in raw if str(r.get("build_id")) == str(contract["build_id"])])
    return list(rows), contract


def make_period_rows_for(
    conn, chart_id: str,
) -> tuple[Callable[[str], list[dict]], dict]:
    """`period_running_at` operand reader for the record grain: agent → that
    lord's MD/AD/PD rows ({start_iso, end_iso}, half-open [start, end) per §4.0)
    from the pinned Vimśottarī read. The read happens once, lazily, on first use;
    the contract that governed it is returned (and filled in once read) so the
    writer can record the build it actually used. A `DashaReadConflict` raised by
    the read propagates — a conflicting daśā read must fail the build, not
    degrade to 'unknown'."""
    state: dict = {"rows": None}
    contract: dict = {"build_id": None, "read": False}

    def rows_for(agent: str, level: str | int | None = None) -> list[dict]:
        """The lord's rows at ONE level (`'md'|'ad'|'pd'` or 1–3) — AM-21: a P1 record is licensed by the periods of its
        ANCHOR lord at its anchor LEVEL — or, with `level=None`, at every level (the legacy union)."""
        if state["rows"] is None:
            rows, c = load_pinned_vimshottari(conn, chart_id)
            state["rows"] = rows
            contract.update(c)
            contract["read"] = True
        want = str(agent).lower()
        want_level = LEVEL_N[level] if isinstance(level, str) else level
        return [
            {"start_iso": r["start_iso"], "end_iso": r["end_iso"]}
            for r in state["rows"]
            if str(r.get("lord_graha", "")).lower() == want
            and (want_level is None or r.get("level_n") == want_level)
        ]

    return rows_for, contract


__all__ = ["PINNED_SYSTEM", "load_pinned_vimshottari", "make_period_rows_for",
           "select_dasha_read_contract"]
