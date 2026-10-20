"""The §4.0 daśā read contract, as ONE implementation (GOCHARA_DESIGN_SPECS_v1_4
§4.0 [L]; ASTRA v1.1 P1-2 / v1.2 P1-1).

Every daśā operand the Gochara family reads from `public.chart_dashas` is pinned
to chart, ayanāṃśa, system, verification tier and ONE build — an unpinned read
is a defect (v1.2 B38-F1). All Kāla and Gochara consumers share this module, including legacy MD
interfaces, F2 clocks, class-context cutover and snapshot projections,
so the rule cannot drift between them (§N.7 item 3: a second
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

from brahmagyan.verification_vocab import RESTRICTED_TABLE_VOCAB, DIVERGENT_FLAGGED
from services.gochara_grammar import dasha_data as DD
from services.gochara_grammar.read_tier_policy import (
    HONEST_COMPUTED_TIERS, LEVEL_TIER_POLICY, row_tier_accepted, tier_accepted)

PINNED_SYSTEM = "vimshottari"
#: the period LEVEL tokens a P1 anchor carries → the chart_dashas `level_n` (§4.0: 1 MD, 2 AD, 3 PD)
LEVEL_N = {"md": 1, "ad": 2, "pd": 3}


SETTLEMENT_PATH = Path(__file__).with_name("dasha_settlement.json")


class DashaBuildRefused(DD.DashaReadConflict):
    """An ungoverned or conflicting daśā read; ``code`` is the typed refusal."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code = code


def _validate_period_bounds(rows):
    """Refuse ordinary admitted ISO periods before consumers lose provenance.

    Date projections may have equal bounds for a positive within-day period;
    only the authoritative ISO instants decide interval validity.
    """
    for row in rows:
        try:
            start, end = row.get("start_iso"), row.get("end_iso")
            if isinstance(start, str):
                start = datetime.fromisoformat(start)
            if isinstance(end, str):
                end = datetime.fromisoformat(end)
            if not isinstance(start, datetime) or not isinstance(end, datetime):
                raise ValueError("no datetime boundary")
            if start.utcoffset() is None or end.utcoffset() is None:
                raise ValueError("boundaries must be timezone-aware")
            if end <= start:
                raise ValueError("non-positive period")
        except (ValueError, TypeError, OverflowError) as exc:
            raise DashaBuildRefused(
                "dasha_period_malformed",
                f"row {row.get('dasha_row_id')}: {exc}") from exc


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


def select_dasha_read_contract(chart_id: str, dasha_periods: list[dict], *, conn=None) -> dict:
    """Bind eligible rows to the receipt's named full run, never to row order."""
    from services.gochara_rules.permission import DASHA_READ_CONTRACT
    from services.gochara_kernel.rehearsal_settlement import settlement_for_connection
    settlement = settlement_for_connection(conn, chart_id, load_dasha_settlement)
    vim = [p for p in dasha_periods if p.get("system_id") == PINNED_SYSTEM]
    if any(p.get("build_id") is None for p in vim):
        raise DashaBuildRefused("dasha_build_null", f"NULL Vimśottarī build for chart {chart_id}")
    builds = sorted({str(p["build_id"]) for p in vim})
    if len(builds) > 1:
        raise DashaBuildRefused("settled_build_ambiguous", f"several eligible builds {builds} for chart {chart_id}")
    build = settlement["run_id"]
    if builds != [build]:
        raise DashaBuildRefused("settled_build_absent", f"named build {build} is not the eligible build for chart {chart_id}")
    contract = {"system_id": PINNED_SYSTEM, "build_id": build,
            "tier": DD.READ_CONTRACT_TIER,
            "ayanamsha_id": DASHA_READ_CONTRACT["ayanamsha_id"],
            "basis": "governed L1_SETTLED receipt and one matching eligible build", "builds_seen": builds}
    if settlement.get("synthetic") is True:
        contract.update(synthetic=True, basis="SYNTHETIC-REHEARSAL-ONLY and one matching eligible build")
    return contract


def _population_query(conn, sql, params):
    try:
        return conn.execute(sql, params).fetchall()
    except Exception as exc:
        raise DashaBuildRefused("dasha_read_unavailable", "daśā population cannot be read") from exc


def assert_single_pinned_build(conn, chart_id: str) -> list[str]:
    """G6: ALL Vimśottarī / lahiri_chitrapaksha rows, every tier and level,
    must carry ONE non-NULL build. A partial rebuild's mixed state is refused
    before filtering. Empty is disclosed by the caller, never a guessed build.
    """
    from services.gochara_rules.permission import DASHA_READ_CONTRACT
    rows = _population_query(conn,
        "SELECT DISTINCT coalesce(build_id::text, 'NULL') FROM public.chart_dashas"
        " WHERE chart_id = %s AND system_id = %s AND ayanamsha_id = %s ORDER BY 1",
        (chart_id, PINNED_SYSTEM, DASHA_READ_CONTRACT["ayanamsha_id"]))
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
    raw = _fetch_dasha_periods_multilevel(
        conn, chart_id, systems=[PINNED_SYSTEM], canonicalize=False)
    contract = select_dasha_read_contract(chart_id, raw, conn=conn)
    contract["raw_vimshottari_rows"] = len(raw)
    rows = _fetch_dasha_periods_multilevel(
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




def _fetch_dasha_periods_multilevel(
    conn,
    chart_id: str,
    ayanamsha_id: str = "lahiri_chitrapaksha",
    systems: list[str] | None = None,
    levels: tuple[int, ...] = DD.DEFAULT_LEVELS,
    tier: str = DD.READ_CONTRACT_TIER,
    build_id: str | None = None,
    canonicalize: bool = True,
    level_tier_policy: bool = False,
) -> list[dict]:
    """Private SQL primitive; only settlement-bound loader entry points call it.

    Select tiers/build before the shared pure duplicate/parent normalization.
    Public consumers must use load_pinned_vimshottari or its governed wrappers.
    """
    if conn is None:
        return []
    want_systems = systems or list(DD.DASHA_SYSTEMS)
    sql = """
            SELECT dasha_row_id, system_id, level_n, parent_row_id,
                   lord_graha, start_iso, end_iso, build_id,
                   verification_pass_status
              FROM chart_dashas
             WHERE chart_id = %s AND ayanamsha_id = %s
               AND system_id = ANY(%s) AND level_n = ANY(%s)
               AND verification_pass_status = {tier_pred}
    """
    if not level_tier_policy:
        tier_pred, tier_param = "%s", tier
    else:  # superset pre-filter; the per-(system, level) policy is applied below
        tier_pred, tier_param = "ANY(%s)", sorted(HONEST_COMPUTED_TIERS | {tier})
    sql = sql.replace("{tier_pred}", tier_pred)
    params: list = [chart_id, ayanamsha_id, want_systems, list(levels), tier_param]
    if build_id is not None:
        sql += "           AND build_id = %s\n"
        params.append(str(build_id))
    sql += "             ORDER BY system_id, level_n, start_iso\n"
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    except Exception as exc:  # noqa: BLE001
        DD.logger.info("[dasha_data] multi-level chart_dashas read failed "
                    "(table unreachable or unpopulated): %s", exc)
        return []
    parsed = [row if isinstance(row, dict) else dict(zip(DD._MULTILEVEL_KEYS, row))
              for row in rows]
    # a row that escaped the pin predicates with a NULL contract field is
    # rejected (never a silently unpinned read)
    # (and a row whose tier the read policy does not accept — defence in depth
    # behind the predicate)
    def _readable(r: dict) -> bool:
        st = r.get("verification_pass_status")
        if level_tier_policy:
            return (row_tier_accepted(r.get("system_id"), r.get("level_n"), st)
                    or tier_accepted(st, {tier}))
        return tier_accepted(st, {tier})
    parsed = [r for r in parsed
              if _readable(r)
              and (build_id is None or str(r.get("build_id")) == str(build_id))]
    if build_id is not None:
        _validate_period_bounds(parsed)
    if not canonicalize:
        # RAW pinned rows — for a caller that must SELECT the build pin
        # first (the §4.0 read contract) and only then canonicalize the
        # pinned set; canonicalizing across builds would reject a foreign
        # build's overlapping rows as conflicts (ASTRA v1.2 P1-1).
        return parsed
    return DD.canonicalize_multilevel_rows(parsed)



def _require_governed_ayanamsha(ayanamsha_id: str) -> None:
    from services.gochara_rules.permission import DASHA_READ_CONTRACT
    if ayanamsha_id != DASHA_READ_CONTRACT["ayanamsha_id"]:
        raise DashaBuildRefused("ayanamsha_not_settled", f"no governed read policy for {ayanamsha_id}")


def _assert_governed_system_builds(conn, chart_id, ayanamsha_id, systems, build):
    """Check every tier and depth BEFORE filtering any requested system."""
    rows = _population_query(conn,
        "SELECT DISTINCT coalesce(build_id::text, 'NULL') FROM public.chart_dashas"
        " WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = ANY(%s) ORDER BY 1",
        (chart_id, ayanamsha_id, list(systems)))
    builds = {str(r[0] if not isinstance(r, dict) else next(iter(r.values()))) for r in rows}
    if len(builds) > 1:
        raise DashaBuildRefused("settled_build_ambiguous", f"mixed requested daśā population: {sorted(builds)}")
    if "NULL" in builds:
        raise DashaBuildRefused("dasha_build_null", "NULL build in requested daśā population")
    if builds and builds != {build}:
        raise DashaBuildRefused("settled_build_absent", "requested daśā population is outside the named run")


def load_governed_dasha_periods(
    conn, chart_id, *, ayanamsha_id="lahiri_chitrapaksha", systems=None,
    levels=DD.DEFAULT_LEVELS, tier=DD.READ_CONTRACT_TIER, build_id=None,
    canonicalize=True, level_tier_policy=False,
):
    """Settlement-bound multi-system equivalent of load_pinned_vimshottari.

    (I) INTERPRETATION: the receipt names one chart/run; other systems must
    belong to that same run. Unnamed charts/ayanamshas have no fallback.
    The existing per-system tier policy is retained, without promotion.
    """
    _require_governed_ayanamsha(ayanamsha_id)
    _, contract = load_pinned_vimshottari(conn, chart_id)
    if tier != DD.READ_CONTRACT_TIER or (build_id is not None and str(build_id) != contract["build_id"]):
        raise DashaBuildRefused("read_contract_mismatch", "caller cannot replace the governed build/tier")
    wanted = list(systems) if systems else list(DD.DASHA_SYSTEMS)
    others = [s for s in wanted if s != PINNED_SYSTEM]
    if others:
        _assert_governed_system_builds(conn, chart_id, ayanamsha_id, others, contract["build_id"])
    # The raw reader is private, and cannot be reached by a legacy caller.
    return _fetch_dasha_periods_multilevel(
        conn, chart_id, ayanamsha_id=ayanamsha_id, systems=wanted,
        levels=levels, tier=tier, build_id=contract["build_id"],
        canonicalize=canonicalize, level_tier_policy=level_tier_policy)


# Legacy projection shapes; execution always goes through the guarded view.
_DASHA_QUERIES = {
    'taranga_md_periods': """
            SELECT lord_graha, start_date, end_date
            FROM chart_dashas
            WHERE chart_id = %s AND ayanamsha_id = %s
              AND system_id = 'vimshottari' AND level_n = 1
            ORDER BY start_date
            """,
    'kshetra_row_count': """SELECT COUNT(*) AS n FROM chart_dashas WHERE chart_id = %s AND system_id = %s""",
    'kshetra_covers_instant': """
        SELECT 1 FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND level_n = %s
          AND start_iso <= %s AND end_iso > %s
        LIMIT 1
        """,
    'kshetra_level1_rows': """
        SELECT dasha_row_id, lord_graha, lord_sign, start_iso, end_iso, duration_days
        FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND level_n = 1
        ORDER BY start_iso ASC
        """,
    'kshetra_kp_twins': """
        SELECT kp.level_n AS level_n,
               (EXISTS (
                   SELECT 1 FROM chart_dashas v
                    WHERE v.chart_id = kp.chart_id
                      AND v.ayanamsha_id = kp.ayanamsha_id
                      AND v.system_id = %s
                      AND v.level_n = kp.level_n
                      AND v.lord_graha IS NOT DISTINCT FROM kp.lord_graha
                      AND abs(extract(epoch FROM (v.start_iso - kp.start_iso))) <= %s
                      AND abs(extract(epoch FROM (v.end_iso   - kp.end_iso)))   <= %s
               )) AS has_twin
          FROM chart_dashas kp
         WHERE kp.chart_id = %s
           AND kp.ayanamsha_id = %s
           AND kp.system_id = %s
           AND kp.start_iso >= %s
           AND kp.end_iso   <= %s
        """,
    'kshetra_boundaries': """
        SELECT dasha_row_id, level_n, lord_graha, lord_sign, parent_row_id,
               start_iso, duration_days
        FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND level_n BETWEEN 1 AND 4
        ORDER BY level_n ASC, start_iso ASC
        """,
    'kshetra_lord_at': """
            SELECT lord_graha, lord_sign FROM chart_dashas
            WHERE chart_id = %s AND system_id = %s AND level_n = %s
              AND start_iso <= %s AND end_iso > %s
            ORDER BY start_iso DESC LIMIT 1
            """,
    'snapshot_consumed_rows': """SELECT d.dasha_row_id::text, d.level_n, d.lord_graha, d.start_iso, d.end_iso FROM public.chart_dashas d JOIN public.ka_gochara_search_input_snapshot s   ON d.chart_id = s.chart_id AND d.dasha_row_id = ANY (s.consumed_dasha_row_ids) WHERE s.chart_id = %s AND s.generation = %s ORDER BY d.level_n, d.start_iso""",
    'dasha_system_counts': """
            SELECT system_id, COUNT(*) AS cnt
            FROM chart_dashas
            WHERE chart_id = %s AND ayanamsha_id = %s
            GROUP BY system_id
            ORDER BY system_id
        """,
    'tree_level1': """
        SELECT dasha_row_id, lord_graha, start_date, end_date,
               kp_sublevel, kp_sub_lord
        FROM chart_dashas
        WHERE chart_id       = %s
          AND ayanamsha_id   = %s
          AND system_id      = %s
          AND level_n        = 1
          AND start_date     < %s
          AND end_date       > %s
        ORDER BY start_date
    """,
    'tree_children': """
        SELECT dasha_row_id, lord_graha, start_date, end_date, level_n,
               parent_row_id, kp_sublevel, kp_sub_lord
        FROM chart_dashas
        WHERE parent_row_id = %s
          AND start_date    < %s
          AND end_date      > %s
        ORDER BY start_date
    """,
    'sweep_birth_anchor': """SELECT MIN(start_date) AS birth_date FROM chart_dashas WHERE chart_id = %s AND level_n = 1""",
    'resonance_candidate_md': """SELECT dasha_row_id,lord_graha,start_iso,end_iso,verification_pass_status
          FROM chart_dashas WHERE chart_id=%s AND build_id=%s AND ayanamsha_id=%s
          AND system_id='vimshottari' AND level_n=1""",
    'resonance_md_lords': """
SELECT DISTINCT lord_graha
FROM chart_dashas
WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = 'vimshottari' AND level_n = 1
  AND lower(lord_graha) = ANY(%s)
""",
    'temporal_timeline': """
        SELECT lord_graha, level_n, start_date, end_date
        FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND ayanamsha_id = %s
          AND level_n <= %s
          AND start_date IS NOT NULL AND end_date IS NOT NULL
    """,
    'permission_spine': """
        SELECT md.dasha_row_id, md.start_date, md.end_date,
               ad.dasha_row_id, ad.start_date, ad.end_date
        FROM chart_dashas md
        JOIN chart_dashas ad ON ad.parent_row_id = md.dasha_row_id
        WHERE md.chart_id = %s AND md.ayanamsha_id = %s
          AND md.system_id = 'vimshottari' AND md.level_n = 1
          AND md.lord_graha = %s
          AND ad.level_n = 2 AND ad.lord_graha = %s
          AND md.start_date <= %s AND md.end_date > %s
          AND ad.start_date <= %s AND ad.end_date > %s
        LIMIT 1
    """,
    'clock_rows': """
        SELECT dasha_row_id, level_n, lord_graha, parent_row_id,
               start_iso, end_iso, build_id, ayanamsha_id, system_id,
               verification_pass_status, applies_to_this_chart_flag,
               is_truncated_at_window_start, is_truncated_at_window_end
        FROM chart_dashas
        WHERE chart_id = %s AND system_id = %s AND ayanamsha_id = %s
          AND level_n BETWEEN 1 AND 4
        ORDER BY level_n ASC, start_iso ASC, dasha_row_id ASC
        """,
    'jivana_md_ad': """
                SELECT lord_graha, start_date, end_date, level_n
                FROM chart_dashas
                WHERE chart_id = %s AND level_n IN (1, 2)
                  AND system_id = 'vimshottari'
                  AND ayanamsha_id = 'lahiri_chitrapaksha'
                ORDER BY start_date, level_n
            """,
    'jivana_pd': """
                SELECT lord_graha, start_date, end_date, level_n
                FROM chart_dashas
                WHERE chart_id = %s
                  AND level_n = 3
                  AND system_id = 'vimshottari'
                  AND ayanamsha_id = 'lahiri_chitrapaksha'
                  AND start_date <= %s
                  AND end_date >= %s
                ORDER BY start_date
            """,
    'sangam_birth_anchor': """SELECT MIN(start_date) AS birth_date FROM chart_dashas WHERE chart_id = %s AND level_n = 1""",
    'taranga_writer_md': """
                SELECT lord_graha, start_date AS ds, end_date AS de
                FROM chart_dashas
                WHERE chart_id = %s AND level_n = 1 AND system_id = 'vimshottari'
                ORDER BY start_date
                """,
    'avadhi_integrity_periods': '''
SELECT * FROM chart_dashas WHERE chart_id=%s AND build_id=%s
  AND ayanamsha_id=%s AND verification_pass_status=%s AND system_id=ANY(%s)
  AND level_n BETWEEN 1 AND 4 ORDER BY system_id,level_n,start_iso,dasha_row_id
''',
    'avadhi_periods': """
SELECT dasha_row_id, system_id, level_n, lord_graha, parent_row_id,
       start_iso, end_iso, start_date, end_date, lord_to_parent_relationship,
       build_id, ayanamsha_id, verification_pass_status, applies_to_this_chart_flag,
       is_truncated_at_window_start, is_truncated_at_window_end
FROM chart_dashas
WHERE chart_id=%s AND ayanamsha_id=%s
  AND system_id=ANY(%s) AND level_n BETWEEN 1 AND 4
ORDER BY system_id, level_n, start_iso, dasha_row_id
""",

}


def dasha_query(name: str) -> str:
    """Return a registered projection, never execute a read."""
    return _DASHA_QUERIES[name]


def execute_governed_dasha_query(
    conn, chart_id, sql, params=(), *, ayanamsha_id="lahiri_chitrapaksha", cursor=None,
    clock_tier=None,
):
    """Read legacy projections from a chart/ayanamsha/build/tier-bound view.

    All-population coherence is checked before the view filters tiers. This
    also governs children-only and aggregate queries whose projection would
    otherwise erase provenance. Uses the caller's transaction and cursor.
    """
    if clock_tier is not None:
        if sql not in (_DASHA_QUERIES["clock_rows"], _DASHA_QUERIES["avadhi_periods"],
                       _DASHA_QUERIES["avadhi_integrity_periods"]):
            raise DashaBuildRefused("read_contract_mismatch", "explicit clock tiers belong to F2 projections")
        if clock_tier not in RESTRICTED_TABLE_VOCAB or clock_tier == DIVERGENT_FLAGGED:
            raise DashaBuildRefused("dasha_tier_refused", "F2 tier is not an admitted honest tier")
    _require_governed_ayanamsha(ayanamsha_id)
    _, contract = load_pinned_vimshottari(conn, str(chart_id))
    _assert_governed_system_builds(
        conn, chart_id, ayanamsha_id, DD.DASHA_SYSTEMS, contract["build_id"])
    # Restrict every reference, including self-joins and nested subqueries.
    projected = re.sub(r"\b(?:public\.)?chart_dashas\b", "governed_chart_dashas", sql, flags=re.I)
    if projected == sql or not re.match(r"\s*SELECT\b", projected, re.I):
        raise DashaBuildRefused("read_contract_mismatch", "unregistered daśā projection")
    # Refuse malformed admitted periods BEFORE any projection can clip,
    # aggregate, select a lord or discard bounds. Never silently filter them.
    # The contract's scope_cap sentinel is excluded by the named period-system
    # allowlist and governed ayanamsha, never by a generic bounds predicate.
    prefix = """WITH governed_chart_dashas AS (
        SELECT * FROM public.chart_dashas
        WHERE chart_id = %s AND ayanamsha_id = %s AND build_id = %s
          AND system_id = ANY(%s) AND level_n BETWEEN 1 AND 4
          AND (verification_pass_status = %s
    """
    bound = [chart_id, ayanamsha_id, contract["build_id"], list(DD.DASHA_SYSTEMS),
             clock_tier if clock_tier is not None else DD.READ_CONTRACT_TIER]
    # F2 has an existing explicit tier contract; vote reads use the per-level policy.
    policy = LEVEL_TIER_POLICY if clock_tier is None else {}
    for (system, level), tiers in sorted(policy.items()):
        prefix += " OR (system_id = %s AND level_n = %s AND verification_pass_status = ANY(%s))"
        bound.extend([system, level, sorted(tiers)])
    prefix += ")) "
    invalid = _population_query(conn, prefix + """
        SELECT dasha_row_id, start_iso, end_iso FROM governed_chart_dashas
        WHERE start_iso IS NULL OR end_iso IS NULL OR end_iso <= start_iso
        LIMIT 1
    """, bound)
    _validate_period_bounds([
        row if isinstance(row, dict) else dict(zip(("dasha_row_id", "start_iso", "end_iso"), row))
        for row in invalid
    ])
    executor = cursor if cursor is not None else conn
    result = executor.execute(prefix + projected, bound + list(params))
    return cursor if cursor is not None else result


def observe_dasha_tiers(conn, chart_id, ayanamsha_id, systems, levels):
    """Settlement-bound diagnostic counts include rejected tiers, never lords.

    ``levels=None`` observes every stored depth, preserving diagnostic counts
    without turning those rows into eligible period operands.
    """
    _require_governed_ayanamsha(ayanamsha_id)
    from services.gochara_kernel.rehearsal_settlement import settlement_for_connection
    settlement = settlement_for_connection(conn, chart_id, load_dasha_settlement)
    _assert_governed_system_builds(conn, chart_id, ayanamsha_id, systems, settlement["run_id"])
    level_sql = " AND level_n = ANY(%s)" if levels is not None else ""
    params = [chart_id, ayanamsha_id, list(systems), settlement["run_id"]]
    if levels is not None:
        params.append(list(levels))
    return conn.execute(
        "SELECT system_id, level_n, verification_pass_status, count(*) AS n"
        " FROM public.chart_dashas WHERE chart_id = %s AND ayanamsha_id = %s"
        " AND system_id = ANY(%s) AND build_id = %s" + level_sql +
        " GROUP BY 1, 2, 3 ORDER BY 1, 2, 3", params)


def validate_live_dasha_periods(chart_id, periods, ayanamsha_id, *, conn=None):
    """Validate preloaded live operands; explicit conn=None fixtures stay pure."""
    _require_governed_ayanamsha(ayanamsha_id)
    contract = select_dasha_read_contract(chart_id, periods, conn=conn)
    for row in periods:
        if row.get("build_id") is None:
            raise DashaBuildRefused("dasha_build_null", "preloaded live operand has no build")
        if str(row["build_id"]) != contract["build_id"]:
            raise DashaBuildRefused("settled_build_ambiguous", "preloaded operands mix build identities")
        try:
            accepted = row_tier_accepted(row.get("system_id"), row.get("level_n"), row.get("verification_pass_status"))
        except (TypeError, ValueError):
            accepted = False
        if not accepted:
            raise DashaBuildRefused("dasha_tier_refused", "preloaded operand has no accepted tier")
    _validate_period_bounds(periods)
    return contract


def make_period_rows_for_snapshot(conn, chart_id: str, generation: str) -> tuple[Callable[[str], list[dict]], dict]:
    """`make_period_rows_for` over the search-input SNAPSHOT's own COPY of the consumed daśā rows (G12, Codex round 1 ruling 3): after the snapshot substep the
    P1 `period_running_at` operand reader never reads live L1, so a rebuild that lands between substeps cannot split the output from the snapshot. The
    contract records the build the COPY carries. A snapshot without a copy (migration 1305 not applied) falls back to the live reader.

    The copy holds only the rows OVERLAPPING the horizon, so on its own it cannot tell a lord the pinned build holds but that runs wholly OUTSIDE the horizon
    (empty running set ⇒ `period_running_at` false) from a lord the build does not hold at all (⇒ unrestricted + `unknown`). The snapshot therefore also
    records, at capture, which (lord, level) pairs the pinned build holds (`consumed_dasha_held`, a jsonb array of {lord, level_n}). `rows_for.holds(agent,
    level)` answers from the copy UNION that record: True ⇒ restrict by the (possibly empty) running rows; False ⇒ the build holds no row for it. A snapshot
    captured before the record existed has `consumed_dasha_held` NULL/absent: `holds` then reads the copy alone (the pre-record behaviour) and
    `contract["held_recorded"]` is False, so nobody mistakes that answer for a measured one (§N.8)."""
    import json
    from datetime import datetime, timezone
    from decimal import Decimal
    has = conn.execute(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'"
        " AND column_name = 'consumed_dasha_rows'").fetchone()
    if int(next(iter(has.values())) if isinstance(has, dict) else has[0]) != 1:
        return make_period_rows_for(conn, chart_id)
    has_held = conn.execute(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'"
        " AND column_name = 'consumed_dasha_held'").fetchone()
    held_col = "consumed_dasha_held::text" if int(next(iter(has_held.values())) if isinstance(has_held, dict) else has_held[0]) == 1 else "NULL::text"
    row = conn.execute(f"SELECT consumed_dasha_rows::text, {held_col} FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s",
                       (chart_id, generation)).fetchone()
    text, held_text = (None, None) if row is None else (tuple(row.values()) if isinstance(row, dict) else tuple(row))
    if text is None:
        return make_period_rows_for(conn, chart_id)
    copy = json.loads(text, parse_float=Decimal)
    held_array = json.loads(held_text) if held_text is not None else None
    held_recorded = isinstance(held_array, list)
    held_pairs = {(str(h["lord"]).lower(), int(h["level_n"])) for h in held_array} if held_recorded else set()
    rows = [{"start_iso": datetime.fromisoformat(e["key"]["start_iso"]).astimezone(timezone.utc),
             "end_iso": datetime.fromisoformat(e["content"]["end_iso"]).astimezone(timezone.utc),
             "lord_graha": e["content"]["lord_graha"], "level_n": int(e["key"]["level_n"]),
             "build_id": str(e["metadata"]["build_id"])} for e in copy if e["key"]["system_id"] == PINNED_SYSTEM]
    builds = sorted({r["build_id"] for r in rows})
    contract = {"build_id": builds[0] if len(builds) == 1 else None, "read": True, "source": "snapshot_copy", "rows": len(rows),
                "builds_in_copy": builds,
                "held_recorded": held_recorded, "held_pairs": len(held_pairs)}

    def rows_for(agent: str, level: str | int | None = None) -> list[dict]:
        want = str(agent).lower()
        want_level = LEVEL_N[level] if isinstance(level, str) else level
        return [{"start_iso": r["start_iso"], "end_iso": r["end_iso"]} for r in rows
                if str(r.get("lord_graha", "")).lower() == want and (want_level is None or r.get("level_n") == want_level)]

    def holds(agent: str, level: str | int | None = None) -> bool:
        """Does the pinned build hold ANY row for (agent, level) — inside the horizon or not? (`level=None`: at any of MD/AD/PD.)"""
        want = str(agent).lower()
        want_level = LEVEL_N[level] if isinstance(level, str) else level
        if rows_for(want, want_level):
            return True
        return any(lord == want and (want_level is None or lv == want_level) for lord, lv in held_pairs)
    rows_for.holds = holds
    return rows_for, contract


__all__ = ["PINNED_SYSTEM", "load_pinned_vimshottari", "make_period_rows_for", "make_period_rows_for_snapshot",
           "select_dasha_read_contract", "load_dasha_settlement", "DashaBuildRefused",
           "load_governed_dasha_periods", "dasha_query", "execute_governed_dasha_query",
           "observe_dasha_tiers", "validate_live_dasha_periods"]
