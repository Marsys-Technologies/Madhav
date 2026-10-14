"""The §4.0 daśā read contract, as ONE implementation (GOCHARA_DESIGN_SPECS_v1_4
§4.0 [L]; ASTRA v1.1 P1-2 / v1.2 P1-1).

Every daśā operand the Gochara family reads from `public.chart_dashas` is pinned
to chart, ayanāṃśa, system, verification tier and ONE build — an unpinned read
is a defect (v1.2 B38-F1). Two consumers read under this contract: the step06a
class-context document (scripts/kala_gochara_cutover, which delegates here) and
the registered '5.0' writer's `period_running_at` prerequisite evaluation. They
share this module so the rule cannot drift between them (§N.7 item 3: a second
copy of the pin logic is a wrapper-local rule that can shadow the first).

The build pin is selected from the chart's single settled build, never a
historical UUID constant. The all-tier guard runs before tier filtering;
several builds or a NULL build are conflicts, never resolved by row order.
The verified read and snapshot then bind the build actually consumed.
"""
from __future__ import annotations

from typing import Callable

from services.gochara_grammar import dasha_data as DD

PINNED_SYSTEM = "vimshottari"
#: the period LEVEL tokens a P1 anchor carries → the chart_dashas `level_n` (§4.0: 1 MD, 2 AD, 3 PD)
LEVEL_N = {"md": 1, "ad": 2, "pd": 3}


def select_dasha_read_contract(chart_id: str, dasha_periods: list[dict]) -> dict:
    """Select the sole verified Vimśottarī build after the all-tier guard.

    The canonical chart still refuses an absent verified population; another
    chart with no rows discloses an empty read. Mixed/NULL builds always refuse.
    """
    from services.gochara_rules.permission import DASHA_READ_CONTRACT
    vim = [p for p in dasha_periods if p.get("system_id") == PINNED_SYSTEM]
    null_build = sum(1 for p in vim if p.get("build_id") is None)
    builds = sorted({str(p.get("build_id")) for p in vim if p.get("build_id") is not None})
    if null_build:
        raise DD.DashaReadConflict(
            f"chart_dashas §4.0: {null_build} two_pass_verified vimshottari rows "
            f"for chart {chart_id} carry a NULL build_id — unpinnable, refusing")
    elif len(builds) == 1:
        build = builds[0]
        basis = "single two_pass_verified build present"
    elif not builds:
        if str(chart_id) == DASHA_READ_CONTRACT["chart_id"]:
            raise DD.DashaReadConflict(
                f"chart_dashas §4.0: no two_pass_verified vimshottari rows for chart {chart_id}")
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


class DashaBuildRefused(DD.DashaReadConflict):
    """G6: the chart's Vimśottarī rows are not a single, pinned build — `code` is `dasha_builds_mixed` or `dasha_build_null`."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


def assert_single_pinned_build(conn, chart_id: str) -> list[str]:
    """G6: ALL Vimśottarī / lahiri_chitrapaksha rows, every tier and level,
    must carry ONE non-NULL build. A partial rebuild's mixed state is refused
    before filtering. Empty is disclosed by the caller, never a guessed build.
    """
    from services.gochara_rules.permission import DASHA_READ_CONTRACT
    rows = conn.execute(
        "SELECT DISTINCT coalesce(build_id::text, 'NULL') FROM public.chart_dashas"
        " WHERE chart_id = %s AND system_id = %s AND ayanamsha_id = %s ORDER BY 1",
        (chart_id, PINNED_SYSTEM, DASHA_READ_CONTRACT["ayanamsha_id"])).fetchall()
    builds = [str(r[0] if not isinstance(r, dict) else next(iter(r.values()))) for r in rows]
    if len(builds) > 1:
        raise DashaBuildRefused("dasha_builds_mixed", f"chart {chart_id} carries Vimśottarī rows of {len(builds)} builds {builds} (every tier): "
                                "a mixed L1 state is not readable — wait for the rebuild to settle")
    if builds == ["NULL"]:
        raise DashaBuildRefused("dasha_build_null", f"chart {chart_id} carries a NULL Vimśottarī build_id — refusing")
    return builds


def load_pinned_vimshottari(conn, chart_id: str) -> tuple[list[dict], dict]:
    """(1) a RAW, non-canonicalized read of the tier-pinned Vimśottarī rows
    selects the build pin; (2) the rows are then fetched PINNED to that build and
    canonicalized — a foreign build's overlapping rows never enter the
    duplicate/conflict pass. Returns (rows, contract); rows is [] when the chart
    has none at the read tier (honest empty — the caller reports 'unknown')."""
    assert_single_pinned_build(conn, chart_id)                     # G6: one non-NULL build, before tier filtering
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
