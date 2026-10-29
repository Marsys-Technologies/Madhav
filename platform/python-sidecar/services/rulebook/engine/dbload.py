"""Rule Book engine (E3/E4) — READ-ONLY loaders for stored operands.

Sources (ENGINE_PLAN §2.2, E0 matrix): ``bg_sky_calendar`` (L0 ingress rows),
``chart_facts`` (L1 natal facts, Lahiri), ``chart_dashas`` (L1 Vimśottarī L1/L2 rows)
and ``charts`` (birth data). Nothing is written: the connection is opened with
``default_transaction_read_only=on`` and every statement is checked to be a SELECT.

A fact that is absent, outside its vocabulary, or returned as more than one row is
a MISSING fact (None -> NOT_ASSESSED) and is counted in ``chart.diagnostics``:
no ORDER BY ever picks a winner among duplicate rows (M10).

Credentials: ``PGPASSWORD`` if set, else the first line of ``~/.pgpass``. The password
is never printed, logged or stored.
"""

from __future__ import annotations

import os
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from . import constants as K
from .birthrecord import L1_BIRTH_MISMATCH, ChartExcluded, ResolvedBirth
from .chart import (
    Birth,
    ChartDataError,
    DashaLevel,
    DashaRow,
    GrahaFacts,
    NatalChart,
    utc_to_jd,
)
from .sky import SkyTable

_READ_ONLY_VERBS = ("select", "with", "show")


class ReadOnlyViolation(RuntimeError):
    pass


def _password() -> Optional[str]:
    pw = os.environ.get("PGPASSWORD")
    if pw:
        return pw
    try:
        with open(Path.home() / ".pgpass", "r", encoding="utf-8") as fh:
            line = fh.readline().rstrip("\n")
        parts = line.split(":")
        return parts[4] if len(parts) >= 5 else None
    except OSError:
        return None


class _ReadOnlyCursor:
    def __init__(self, cur: Any):
        self._cur = cur

    def execute(self, sql: str, params: Any = None) -> "_ReadOnlyCursor":
        head = sql.lstrip().split(None, 1)[0].lower() if sql.strip() else ""
        if head not in _READ_ONLY_VERBS:
            raise ReadOnlyViolation(f"only SELECT is allowed here, got {head!r}")
        self._cur.execute(sql, params)
        return self

    def fetchall(self) -> List[Any]:
        return self._cur.fetchall()

    def fetchone(self) -> Any:
        return self._cur.fetchone()

    def __enter__(self) -> "_ReadOnlyCursor":
        return self

    def __exit__(self, *exc: Any) -> None:
        self._cur.close()


class ReadOnlyConnection:
    def __init__(self, conn: Any):
        self._conn = conn

    def cursor(self) -> _ReadOnlyCursor:
        return _ReadOnlyCursor(self._conn.cursor())

    def close(self) -> None:
        self._conn.close()


def connect_readonly(host: str = "127.0.0.1", port: int = 5433, dbname: str = "amjis", user: str = "amjis_app") -> ReadOnlyConnection:
    import psycopg

    pw = _password()
    conn = psycopg.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=pw,
        connect_timeout=10,
        options="-c default_transaction_read_only=on",
        autocommit=True,
    )
    with conn.cursor() as cur:
        cur.execute("show default_transaction_read_only")
        if cur.fetchone()[0] != "on":
            conn.close()
            raise ReadOnlyViolation("session is not read-only; refusing to continue")
    return ReadOnlyConnection(conn)


# ── sky ────────────────────────────────────────────────────────────────────
def load_sky(conn: ReadOnlyConnection) -> SkyTable:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, event_type, primary_body, sign, event_jd FROM bg_sky_calendar "
            "WHERE event_type = 'ingress' AND ayanamsha_key = %s ORDER BY event_jd",
            (K.AYANAMSHA_L0,),
        )
        rows = [
            {"id": r[0], "event_type": r[1], "primary_body": r[2], "sign": r[3], "event_jd": r[4]} for r in cur.fetchall()
        ]
    return SkyTable(rows)


# ── chart ──────────────────────────────────────────────────────────────────
_FACT_SQL = (
    "SELECT fact_id, fact_category, fact_subject, fact_key, fact_value_text, fact_value_num, fact_value_jsonb "
    "FROM chart_facts WHERE chart_id = %s AND ayanamsha_id = %s AND "
    "((fact_category = 'graha_position' AND fact_key IN ('sign','retrograde_flag','longitude_sidereal')) "
    "OR (fact_category = 'graha_special_state_rollup' AND fact_key IN ('is_exalted','is_debilitated')) "
    "OR (fact_category = 'graha_dignity_per_varga' AND fact_key = 'dignity_state' AND fact_subject LIKE 'D1\\_%%') "
    "OR (fact_category = 'aspect_parashari_given') "
    "OR (fact_category = 'lord_in_house_per_varga' AND fact_subject LIKE 'D1\\_H%%' AND fact_key = 'lord_placement'))"
)


def load_chart(conn: ReadOnlyConnection, chart_id: str, resolved: Optional[ResolvedBirth] = None) -> NatalChart:
    """Load one chart's natal operands and Vimśottarī L1/L2 rows. Read-only.

    ``resolved`` (explicit-offset path, see ``birthrecord``): the birth instant comes from the source
    record's stated UT offset, not from ``charts.timezone_id``. The stored chart row must describe the
    same local birth, else the chart is excluded (L1_BIRTH_MISMATCH).
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT birth_date, birth_time, birth_lat, birth_lng, timezone_id, ayanamsa FROM charts WHERE chart_id = %s",
            (chart_id,),
        )
        rows = cur.fetchall()
        if len(rows) != 1:
            raise ChartDataError(f"charts: {len(rows)} rows for chart_id (need exactly 1)")
        bdate, btime, lat, lng, tz, ayan = rows[0]
        if ayan != K.AYANAMSHA_L0:
            raise ChartDataError(f"chart ayanāṃśa is {ayan!r}; the engine reads Lahiri only")
        if btime is None:
            raise ChartDataError("chart has no birth time")
        cur.execute(_FACT_SQL, (chart_id, K.AYANAMSHA_L1))
        facts = cur.fetchall()
        cur.execute(
            "SELECT level_n, lord_graha, start_iso, end_iso, dasha_row_id FROM chart_dashas "
            "WHERE chart_id = %s AND ayanamsha_id = %s AND system_id = %s AND level_n IN (1, 2) ORDER BY start_iso",
            (chart_id, K.AYANAMSHA_L1, K.DASHA_SYSTEM),
        )
        dasha_rows = cur.fetchall()
    birth = Birth(
        birth_date=bdate,
        birth_time_local=btime.strftime("%H:%M:%S") if isinstance(btime, time) else str(btime),
        lat=float(lat),
        lon=float(lng),
        zone=tz,
    )
    if resolved is not None:
        r = resolved.record
        stored_t = birth.birth_time_local if birth.birth_time_local.count(":") == 2 else birth.birth_time_local + ":00"
        want_t = r.local_time if r.local_time.count(":") == 2 else r.local_time + ":00"
        if bdate != r.local_date or stored_t != want_t or abs(birth.lat - r.lat) > 1e-3 or abs(birth.lon - r.lon) > 1e-3:
            raise ChartExcluded(L1_BIRTH_MISMATCH, "the stored chart row is not the record's local birth")
        birth = resolved.birth()
    return build_chart(chart_id, birth, facts, dasha_rows)


def build_chart(
    chart_key: str,
    birth: Birth,
    facts: Iterable[Sequence[Any]],
    dasha_rows: Iterable[Sequence[Any]],
) -> NatalChart:
    """Assemble a NatalChart from fact rows (pure; unit-testable without a database).

    ``facts`` rows: (fact_id, category, subject, key, value_text, value_num, value_jsonb).
    ``dasha_rows`` rows: (level_n, lord_graha, start_iso, end_iso, row_id).
    """
    diag: Dict[str, int] = {}
    ledger: Dict[str, List[str]] = {"chart_facts": [], "chart_dashas": []}
    grouped: Dict[Tuple[str, str, str], List[Sequence[Any]]] = {}
    for r in facts:
        grouped.setdefault((r[1], r[2], r[3]), []).append(r)

    def one(cat: str, subj: str, key: str) -> Optional[Sequence[Any]]:
        rows = grouped.get((cat, subj, key)) or []
        if not rows:
            return None
        if len(rows) > 1:
            diag["non_unique_fact"] = diag.get("non_unique_fact", 0) + 1
            return None
        ledger["chart_facts"].append(str(rows[0][0]))
        return rows[0]

    def sign_of(subject: str) -> Optional[int]:
        r = one("graha_position", subject, "sign")
        if r is None:
            return None
        n = K.SIGN_NUMBER.get(r[4])
        if n is None:
            diag["unknown_sign_vocabulary"] = diag.get("unknown_sign_vocabulary", 0) + 1
        return n

    def flag(cat: str, subject: str, key: str) -> Optional[bool]:
        r = one(cat, subject, key)
        if r is None:
            return None
        v = K.BOOL_TEXT.get(str(r[4]).lower()) if r[4] is not None else None
        if v is None:
            diag["unknown_bool_vocabulary"] = diag.get("unknown_bool_vocabulary", 0) + 1
        return v

    grahas: Dict[str, GrahaFacts] = {}
    for g in K.GRAHAS:
        subj = K.CF_SUBJECT[g]
        rr = one("graha_position", subj, "retrograde_flag")
        retro = None
        if rr is not None:
            retro = K.RETROGRADE_FLAG_VALUES.get(rr[4])
            if retro is None:
                diag["unknown_retrograde_vocabulary"] = diag.get("unknown_retrograde_vocabulary", 0) + 1
        dg = one("graha_dignity_per_varga", f"D1_{subj}", "dignity_state")
        lr = one("graha_position", subj, "longitude_sidereal")
        grahas[g] = GrahaFacts(
            longitude=float(lr[5]) if lr is not None and lr[5] is not None else None,
            sign=sign_of(subj),
            retrograde=retro,
            exalted=flag("graha_special_state_rollup", subj, "is_exalted"),
            debilitated=flag("graha_special_state_rollup", subj, "is_debilitated"),
            dignity_state=dg[4] if dg is not None else None,
        )
    lagna = sign_of("LAGNA")

    aspected: Dict[str, Optional[frozenset]] = {}
    for g in K.GRAHAS:
        subj = K.CF_SUBJECT[g]
        hs = set()
        for (cat, s, key), rows in grouped.items():
            if cat == "aspect_parashari_given" and s == subj and key.startswith("house_"):
                if len(rows) != 1:
                    diag["non_unique_fact"] = diag.get("non_unique_fact", 0) + 1
                    hs = None  # type: ignore[assignment]
                    break
                try:
                    hs.add(int(key.split("_", 1)[1]))
                except ValueError:
                    diag["unknown_aspect_key"] = diag.get("unknown_aspect_key", 0) + 1
                    continue
                ledger["chart_facts"].append(str(rows[0][0]))
        # every graha casts at least the 7th-house aspect, so an empty set means the rows are missing
        aspected[g] = frozenset(hs) if hs else None

    lords: Dict[int, Optional[str]] = {}
    for h in range(1, 13):
        r = one("lord_in_house_per_varga", f"D1_H{h}", "lord_placement")
        lord = None
        if r is not None:
            js = r[6] if isinstance(r[6], Mapping) else {}
            lord = K.CARD_GRAHA_BY_L0_BODY.get(js.get("lord"))
            if lord is None:
                diag["unknown_lord_vocabulary"] = diag.get("unknown_lord_vocabulary", 0) + 1
        lords[h] = lord

    md_rows: List[DashaRow] = []
    ad_rows: List[DashaRow] = []
    for level, lord_name, start, end, row_id in dasha_rows:
        lord = K.CARD_GRAHA_BY_L0_BODY.get(lord_name)
        if lord is None:
            raise ChartDataError(f"daśā lord {lord_name!r} not recognised")
        row = DashaRow(lord, utc_to_jd(start), utc_to_jd(end))
        (md_rows if level == K.DASHA_LEVEL_MD else ad_rows).append(row)
        ledger["chart_dashas"].append(str(row_id))
    return NatalChart(
        chart_key=chart_key,
        birth=birth,
        lagna_sign=lagna,
        grahas=grahas,
        aspected_houses=aspected,
        house_lords=lords,
        md=DashaLevel(md_rows),
        ad=DashaLevel(ad_rows),
        ledger=ledger,
        diagnostics=diag,
    )
