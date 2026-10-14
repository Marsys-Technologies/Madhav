"""The §4.0 daśā read contract, as ONE implementation (GOCHARA_DESIGN_SPECS_v1_4
§4.0 [L]; ASTRA v1.1 P1-2 / v1.2 P1-1).

Every daśā operand the Gochara family reads from `public.chart_dashas` is pinned
to chart, ayanāṃśa, system, verification tier and ONE build — an unpinned read
is a defect (v1.2 B38-F1). Two consumers read under this contract: the step06a
class-context document (scripts/kala_gochara_cutover, which delegates here) and
the registered '5.0' writer's `period_running_at` prerequisite evaluation. They
share this module so the rule cannot drift between them (§N.7 item 3: a second
copy of the pin logic is a wrapper-local rule that can shadow the first).

The build pin comes from the reviewed dasha_settlement.json receipt, validated
against the eligible rows, never from a historical UUID constant or row order. The all-tier guard runs before tier filtering;
several builds or a NULL build are conflicts, never resolved by row order.
The verified read and snapshot then bind the build actually consumed.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from uuid import UUID
from typing import Callable

from services.gochara_grammar import dasha_data as DD

PINNED_SYSTEM = "vimshottari"
#: the period LEVEL tokens a P1 anchor carries → the chart_dashas `level_n` (§4.0: 1 MD, 2 AD, 3 PD)
LEVEL_N = {"md": 1, "ad": 2, "pd": 3}


SETTLEMENT_PATH = Path(__file__).with_name("dasha_settlement.json")


class DashaBuildRefused(DD.DashaReadConflict):
    """An ungoverned or conflicting daśā read; ``code`` is the typed refusal."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


def load_dasha_settlement(chart_id: str) -> dict:
    """Load the reviewed receipt on each read; no row-presence or cached fallback."""
    try:
        text = SETTLEMENT_PATH.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise DashaBuildRefused("settlement_malformed", "governed settlement is not UTF-8") from exc
    except OSError as exc:
        raise DashaBuildRefused("settlement_missing", "governed settlement is absent or unreadable") from exc
    try:
        record = json.loads(text)
        if not isinstance(record, dict) or record["schema"] != "gochara_dasha_settlement/1":
            raise ValueError("invalid settlement schema")
        if not isinstance(record["header_comment"], str) or "reviewed PR" not in record["header_comment"]:
            raise ValueError("missing review policy")
        match = re.fullmatch(
            r"L1_SETTLED v1 utc=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) "
            r"pos_build=([0-9a-f]{8}) dash_build=([0-9a-f]{8}) natal_fp=([0-9a-f]{8}) "
            r"vim13_fp=([0-9a-f]{8}) vim13_rows=([0-9]+) dash_all_fp=([0-9a-f]{8})",
            record["line"])
        if match is None:
            raise ValueError("invalid L1_SETTLED line")
        keys = ("utc", "pos_build", "dash_build", "natal_fp", "vim13_fp", "vim13_rows", "dash_all_fp")
        parsed = dict(zip(keys, match.groups()))
        parsed["vim13_rows"] = int(parsed["vim13_rows"])
        if type(record["vim13_rows"]) is not int or record["vim13_rows"] <= 0:
            raise ValueError("invalid row count")
        if any(record[key] != value for key, value in parsed.items()):
            raise ValueError("L1_SETTLED line disagrees with parsed fields")
        datetime.strptime(record["utc"], "%Y-%m-%dT%H:%M:%SZ")
        for key in ("run_id", "chart_id"):
            if str(UUID(record[key])) != record[key]:
                raise ValueError("invalid UUID")
        if record["run_id"][:8] != record["dash_build"]:
            raise ValueError("dash_build is not the run prefix")
        provenance = record["provenance"]
        if (not isinstance(provenance, dict)
                or provenance["source"] != "origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md"
                or re.fullmatch(r"[0-9a-f]{40}", provenance["commit"]) is None
                or provenance["heading"] != "L1_SETTLED v1"
                or not isinstance(provenance["release_receipt"], str) or not provenance["release_receipt"]
                or provenance["rebuild_run"] != record["run_id"]):
            raise ValueError("invalid settlement provenance")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise DashaBuildRefused("settlement_malformed", "governed settlement failed shape/line validation") from exc
    if str(chart_id) != record["chart_id"]:
        raise DashaBuildRefused("chart_not_settled", f"no settlement entry for chart {chart_id}")
    return record


def select_dasha_read_contract(chart_id: str, dasha_periods: list[dict]) -> dict:
    """Bind eligible rows to the receipt's named full run, never to row order."""
    from services.gochara_rules.permission import DASHA_READ_CONTRACT
    settlement = load_dasha_settlement(chart_id)
    vim = [p for p in dasha_periods if p.get("system_id") == PINNED_SYSTEM]
    if any(p.get("build_id") is None for p in vim):
        raise DashaBuildRefused("dasha_build_null", f"NULL Vimśottarī build for chart {chart_id}")
    builds = sorted({str(p["build_id"]) for p in vim})
    if len(builds) > 1:
        raise DashaBuildRefused("settled_build_ambiguous", f"several eligible builds {builds} for chart {chart_id}")
    build = settlement["run_id"]
    if builds != [build]:
        raise DashaBuildRefused("settled_build_absent", f"named build {build} is not the eligible build for chart {chart_id}")
    return {"system_id": PINNED_SYSTEM, "build_id": build,
            "tier": DD.READ_CONTRACT_TIER,
            "ayanamsha_id": DASHA_READ_CONTRACT["ayanamsha_id"],
            "basis": "governed L1_SETTLED receipt and one matching eligible build", "builds_seen": builds}


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
        raise DashaBuildRefused("settled_build_ambiguous", f"chart {chart_id} carries Vimśottarī rows of {len(builds)} builds {builds} (every tier): "
                                "a mixed L1 state is not readable — wait for the rebuild to settle")
    if builds == ["NULL"]:
        raise DashaBuildRefused("dasha_build_null", f"chart {chart_id} carries a NULL Vimśottarī build_id — refusing")
    return builds


def load_pinned_vimshottari(conn, chart_id: str) -> tuple[list[dict], dict]:
    """(1) a RAW, non-canonicalized read of the tier-pinned Vimśottarī rows
    selects the build pin; (2) the rows are then fetched PINNED to that build and
    canonicalized — a foreign build's overlapping rows never enter the
    duplicate/conflict pass. Returns (rows, contract); missing settlement or eligible rows refuses."""
    assert_single_pinned_build(conn, chart_id)                     # G6: one non-NULL build, before tier filtering
    raw = DD.fetch_dasha_periods_multilevel(
        conn, chart_id, systems=[PINNED_SYSTEM], canonicalize=False)
    contract = select_dasha_read_contract(chart_id, raw)
    contract["raw_vimshottari_rows"] = len(raw)
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
           "select_dasha_read_contract", "load_dasha_settlement", "DashaBuildRefused"]
