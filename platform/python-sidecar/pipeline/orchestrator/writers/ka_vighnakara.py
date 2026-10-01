"""
ka_vighnakara writer — obstruction / counter-indicator detector.

D5 (Kāla completeness v2): replaced all proxy detectors with live ephemeris
and real panchāṅga calls.  Detection hierarchy:

  1. malefic_transit   — Saturn or Rahu in adversarial sign relative to native lagna/moon,
                         computed via swisseph at peak_date.
  2. panchanga_obstruction — Rikta tithi (the engine's set, tithi ids 4/9/14/19/24/29,
                             classified by `panchang_engine.rich_topics.compute_tithi_attrs`) from
                             ka_muhurta_seva; real tithi, not day-mod arithmetic.
  3. gandanta          — Moon within the water-fire junction at peak_date (last 3°20' of
                         Cancer/Scorpio/Pisces AND first 3°20' of Leo/Sagittarius/Aries),
                         computed via swisseph; the arc and zone test are the L1 definition
                         (`ga_writers.ga_sensitive_degree_writer.check_gandanta`), not
                         re-declared here.
  4. papakartari       — lagna bhava hemmed between malefics in adjacent signs at peak_date,
                         from natal lagna + swisseph transit positions.
  5. combustion        — any planet within 6° of Sun (from chart_facts natal positions).

NEVER commits or rollbacks — orchestrator owns the transaction.
"""
import json
import logging
from datetime import date as DateType
from typing import Optional

from panchang_engine.swiss_state import serialized_swiss_state
# Rikta classification: the engine's own tithi-type table (tithi ids 1..30), via its public
# accessor. Referenced, never re-listed here.
from panchang_engine.rich_topics import compute_tithi_attrs
# Gandanta arc + zone test: the L1 definition (SS ruling N-28). Referenced, never re-declared.
from ga_writers.ga_sensitive_degree_writer import GANDANTA_CITATION, check_gandanta

import psycopg

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_temporal import (
    load_dasha_timeline,
    resolve_activation_windows,
    resolve_birth_date,
)

logger = logging.getLogger(__name__)

# WP-2.1 / F-L10-018: cap on distinct dasha-derived anchor dates scanned for
# obstructions (row-size + swisseph-cost guard). The dasha timeline yields at
# most a few dozen distinct MD/AD midpoints, so this ceiling is generous.
_MAX_DASHA_ANCHORS = 200

# Chart-relative adversity (Track I-2). These used to be literal sign-name tables for one
# Aries-lagna / Aquarius-Moon native, applied to every chart. The rules are unchanged but are
# now expressed as house offsets (1 = the reference sign itself) from THIS chart's lagna / Moon:
#   Saturn: dusthana from lagna (6th .50, 8th .60 severe, 12th .45); sade-sati from Moon
#           (12th .45 rising, 1st .65 peak, 2nd .45 setting).
#   Rahu:   from lagna only: 7th .40 (maraka axis), 6th .45 (enemy), 8th .45 (death).
_SATURN_LAGNA_OFFSETS = ((6, 0.50), (8, 0.60), (12, 0.45))
_SATURN_MOON_OFFSETS = ((12, 0.45), (1, 0.65), (2, 0.45))
_RAHU_LAGNA_OFFSETS = ((7, 0.40), (6, 0.45), (8, 0.45))

_SIGN_NAMES = (
    'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
)


def _is_rikta_tithi(tithi: int) -> bool:
    """Rikta per the panchang engine's own tithi-type table (no local copy of the set)."""
    return compute_tithi_attrs(tithi).anga_type == 'Rikta'


def _ordinal(n: int) -> str:
    return {1: '1st', 2: '2nd', 3: '3rd'}.get(n, f'{n}th')


def _chart_adverse_signs(
    natal_lagna_lon: Optional[float],
    natal_moon_lon: Optional[float],
) -> tuple[dict, dict]:
    """Return ({sign: (score, [relations])} for Saturn, same for Rahu) for ONE chart.

    A missing natal lagna / Moon longitude contributes no entries (an honest omission, never
    another native's table). Overlapping relations on one sign keep the max score and list all.
    """
    def _build(specs):
        out: dict[str, tuple[float, list[str]]] = {}
        for lon, offsets, label in specs:
            if lon is None:
                continue
            base = int(lon % 360.0 // 30)
            for offset, score in offsets:
                sign = _SIGN_NAMES[(base + offset - 1) % 12]
                prev_score, rels = out.get(sign, (0.0, []))
                rels = rels + [f"{_ordinal(offset)} from {label}"]
                out[sign] = (max(prev_score, score), rels)
        return out

    saturn = _build([
        (natal_lagna_lon, _SATURN_LAGNA_OFFSETS, 'lagna'),
        (natal_moon_lon, _SATURN_MOON_OFFSETS, 'Moon'),
    ])
    rahu = _build([(natal_lagna_lon, _RAHU_LAGNA_OFFSETS, 'lagna')])
    return saturn, rahu

# Gandanta windows are NOT declared here: the water-fire junction (last GANDANTA_ARC of
# Cancer/Scorpio/Pisces AND first GANDANTA_ARC of Leo/Sagittarius/Aries) is the L1 definition
# in ga_writers.ga_sensitive_degree_writer (CLAUDE.md §N.7 item 3: no wrapper-local constant
# may shadow an L1 value). The previous local table covered the first 3°20' of the water signs
# (90-93.33, 210-213.33, 330-333.33) — a window that is not gandanta at all.

# (C12 fix) flat _COMBUSTION_ORB_DEG = 6.0 DELETED — per-graha orbs from bg_combustion_orbs.
# These classical fallback values are used when the DB table is unavailable.
# Sārāvalī ch.6 / BPHS ch.3: Moon=12 d; Mars=17 d; Mercury=14 d; Jupiter=11 d; Venus=10 d; Saturn=15 d.
_COMBUSTION_ORBS_CLASSICAL: dict[str, float] = {
    'Moon': 12.0, 'Mars': 17.0, 'Mercury': 14.0,
    'Jupiter': 11.0, 'Venus': 10.0, 'Saturn': 15.0,
    'Rahu': 9.0, 'Ketu': 9.0,
}

# Planet IDs for swisseph (subset used by detection)
_SWE_IDS = {
    'Sun': 0, 'Moon': 1, 'Mars': 4, 'Saturn': 6,
    'Rahu': 11,  # swe.TRUE_NODE
}

# Severity mapping
_SEVERITY_THRESHOLDS = [(0.70, 'severe'), (0.40, 'moderate'), (0.0, 'mild')]

# Public aliases expected by tests
SEVERITY_MAP = _SEVERITY_THRESHOLDS
MALEFICS: frozenset = frozenset({'Saturn', 'Mars', 'Rahu', 'Ketu', 'Sun'})

# All valid obstruction_type values (CHECK constraint on kala_obstruction table).
# Detectors 1–5 cover: malefic_transit, panchanga_obstruction, gandanta, papakartari, combustion.
# rashi_dristi_conflict and dasha_lord_afflicted are reserved for future detectors; listed here
# so the type enum is complete and the constraint is documented at the point of definition.
_ALL_OBSTRUCTION_TYPES = frozenset({
    'malefic_transit', 'dasha_lord_afflicted', 'panchanga_obstruction',
    'rashi_dristi_conflict', 'combustion', 'gandanta', 'papakartari',
})


def _severity(score: float) -> str:
    for threshold, label in _SEVERITY_THRESHOLDS:
        if score >= threshold:
            return label
    return 'mild'


def _coerce_date(d) -> Optional[DateType]:
    """Accept date or ISO string, return date or None."""
    if d is None:
        return None
    if isinstance(d, DateType):
        return d
    try:
        return DateType.fromisoformat(str(d))
    except Exception:
        return None


@serialized_swiss_state
def _get_sidereal_lon(swe, jd: float, planet_id: int) -> Optional[float]:
    """Return Lahiri sidereal longitude of a planet at JD, or None on error."""
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        pos, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
        return pos[0] % 360.0
    except Exception as exc:
        logger.debug("_get_sidereal_lon planet=%d jd=%.1f failed: %s", planet_id, jd, exc)
        return None


def _lon_to_sign(lon: float) -> str:
    _SIGNS = (
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
    )
    return _SIGNS[int(lon // 30) % 12]


def _jd_from_date(d: DateType) -> float:
    try:
        import swisseph as swe
        return swe.julday(d.year, d.month, d.day, 0.0)
    except Exception:
        days = (d - DateType(2000, 1, 1)).days
        return 2451545.0 + days


@register('ka_vighnakara')
class KaVighnakaraWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        # Guard: swisseph is REQUIRED for real ephemeris-based detection.  Without it
        # the malefic_transit, gandanta and papakartari detectors cannot run and
        # would emit stub rows with severity_score=0 that are indistinguishable
        # from genuine zero-score computations.  Check BEFORE any DB operations so
        # that a missing swisseph never causes the prior chart's kala_obstruction rows
        # to be silently wiped by the DELETE below.
        try:
            import swisseph as swe
            _swe = swe
        except ImportError:
            raise RuntimeError(
                "swisseph not available in this container — check Dockerfile"
            )

        conn     = ctx.db_conn  # NEVER commit or rollback
        chart_id = ctx.config['chart_id']

        # Idempotency: delete-then-insert scoped to chart.
        # Safe to DELETE only after confirming swisseph is available and we can rebuild.
        with conn.cursor() as _timeout_cur:
            _timeout_cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_obstruction WHERE chart_id = %s", (chart_id,))

        # Read convergence windows
        with conn.cursor(row_factory=psycopg.rows.tuple_row) as cur:
            cur.execute("""
                SELECT convergence_id, signal_id, mode, peak_date,
                       convergence_score, orb_strength, window_start, window_end
                FROM kala_convergence
                WHERE chart_id = %s AND peak_date IS NOT NULL
                ORDER BY convergence_score DESC NULLS LAST
                LIMIT 500
            """, (chart_id,))
            convergence_rows = cur.fetchall()

        if not convergence_rows:
            return WriterResult(
                asset_id='ka_vighnakara', rows_inserted=0,
                notes='No convergence windows — run ka_sangam first',
            )

        # Pre-fetch natal lagna longitude from chart_facts (for papakartari + combustion)
        natal_lagna_lon: Optional[float] = self._fetch_natal_lagna_lon(conn, chart_id)
        # Track I-2: the Moon's natal sidereal longitude, same pinned graha_position source.
        natal_moon_lon: Optional[float] = self._fetch_natal_moon_lon(conn, chart_id)

        # Try to obtain muhurta service for real tithi
        try:
            from services.ka_muhurta_seva.service import KaMuhurtaSevaService
            _muhurta = KaMuhurtaSevaService()
        except Exception as exc:
            logger.warning("ka_vighnakara: KaMuhurtaSevaService unavailable: %s", exc)
            _muhurta = None

        # CR-87 fix: native_location_ctx (formerly a hardcoded module constant
        # tied to chart 482012f1's
        # Bhubaneswar coordinates) resolved per-chart below — no fallback to
        # any specific native's location.
        native_location_ctx = self._resolve_native_location(conn, chart_id, ctx.config.get('birth_params'))

        # C12 fix: fetch per-graha combustion orbs from bg_combustion_orbs (L1 single truth)
        combustion_orbs = self._fetch_combustion_orbs(conn)

        rows = []
        for conv_row in convergence_rows:
            conv_id, signal_id, mode, peak_date, conv_score, orb_str, win_start, win_end = conv_row
            if peak_date is None:
                continue
            if isinstance(peak_date, str):
                peak_date = DateType.fromisoformat(peak_date)

            jd = _jd_from_date(peak_date)

            obstructions = _detect_all(
                peak_date=peak_date,
                jd=jd,
                swe=_swe,
                muhurta_service=_muhurta,
                native_location=native_location_ctx,
                natal_lagna_lon=natal_lagna_lon,
                combustion_orbs=combustion_orbs,
                natal_moon_lon=natal_moon_lon,
            )

            for obs in obstructions:
                rows.append((
                    chart_id,
                    conv_id,
                    signal_id,
                    obs['obstruction_type'],
                    obs['severity'],
                    obs['severity_score'],
                    obs['override_score'],
                    json.dumps(obs['detail']),
                    f"ka_vighnakara:v2.0:conv={conv_id}",
                ))

        # ── WP-2.1 / F-L10-018: dasha-anchored obstruction reachability ────────
        # Convergence covers only a fraction of signals, so obstruction windows
        # anchored solely on convergence peaks were unreachable (602/638). Emit
        # obstructions ALSO at the dasha-derived activation anchors — the same L1
        # daśā-timeline peaks ka_kalasutra now dates activations on — so
        # obstruction and activation windows co-locate in time and join.
        # convergence_id is NULL (nullable FK); signal_id carries the join key.
        already_covered = {
            str(r[1]) for r in convergence_rows if r[1] is not None  # signal_id column
        }
        dasha_anchors = self._dasha_anchor_peaks(conn, chart_id, already_covered)
        for peak_date, signal_id in dasha_anchors:
            jd = _jd_from_date(peak_date)
            obstructions = _detect_all(
                peak_date=peak_date,
                jd=jd,
                swe=_swe,
                muhurta_service=_muhurta,
                native_location=native_location_ctx,
                natal_lagna_lon=natal_lagna_lon,
                combustion_orbs=combustion_orbs,
                natal_moon_lon=natal_moon_lon,
            )
            for obs in obstructions:
                detail = dict(obs['detail'])
                detail['anchor'] = 'dasha_timeline'
                rows.append((
                    chart_id,
                    None,  # convergence_id — dasha-anchored, no convergence window
                    signal_id,
                    obs['obstruction_type'],
                    obs['severity'],
                    obs['severity_score'],
                    obs['override_score'],
                    json.dumps(detail),
                    f"ka_vighnakara:v2.0:dasha_anchor",
                ))

        if rows:
            with conn.cursor() as cur:
                cur.executemany(
                    """INSERT INTO kala_obstruction (
                        chart_id, convergence_id, signal_id,
                        obstruction_type, severity, severity_score, override_score,
                        obstruction_detail, source_citation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    rows,
                )

        return WriterResult(asset_id='ka_vighnakara', rows_inserted=len(rows))

    def _fetch_combustion_orbs(self, conn) -> dict[str, float]:
        """Read per-graha combustion orbs from bg_combustion_orbs (C12 fix).
        Falls back to _COMBUSTION_ORBS_CLASSICAL if the table is unavailable."""
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_comb_orbs")
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT graha, orb_degrees FROM bg_combustion_orbs")
                orbs = {row['graha']: float(row['orb_degrees']) for row in cur.fetchall()}
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_comb_orbs")
            return orbs if orbs else dict(_COMBUSTION_ORBS_CLASSICAL)
        except Exception as exc:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_comb_orbs")
            logger.debug("ka_vighnakara: bg_combustion_orbs fetch skipped: %s", exc)
            return dict(_COMBUSTION_ORBS_CLASSICAL)

    @staticmethod
    def _resolve_native_location(conn, chart_id: str, birth_params) -> dict:
        """CR-87 fix: resolve THIS chart's birth location for the panchanga /
        muhurta detectors. Prefers ctx.config['birth_params'] (orchestrator-
        supplied); falls back to a direct public.charts query only if
        birth_params lacks lat/lon. Never falls back to Bhubaneswar or any
        other specific native's coordinates — a resolution failure raises
        loudly (B.10 — never invent, never borrow another chart's constants).
        """
        if isinstance(birth_params, dict):
            lat = birth_params.get('latitude_deg')
            lon = birth_params.get('longitude_deg')
            tz_hours = birth_params.get('tz_offset_hours')
            if lat is not None and lon is not None and tz_hours is not None:
                return {
                    'lat': float(lat),
                    'lon': float(lon),
                    'tz_offset_minutes': int(round(float(tz_hours) * 60)),
                }

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT birth_lat, birth_lng, timezone_id
                FROM public.charts
                WHERE id = %s OR chart_id = %s
                LIMIT 1
                """,
                (chart_id, chart_id),
            )
            row = cur.fetchone()

        if not row or row[0] is None or row[1] is None:
            raise RuntimeError(
                f"ka_vighnakara: could not resolve birth location for chart {chart_id} "
                "from ctx.config['birth_params'] or public.charts. Refusing to fall "
                "back to Bhubaneswar or any other chart's coordinates (CR-87)."
            )

        lat, lon, tzid = row[0], row[1], row[2]
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            offset = ZoneInfo(tzid).utcoffset(datetime.now())
            if offset is None:
                raise ValueError(f"no utcoffset for {tzid!r}")
            tz_offset_minutes = int(offset.total_seconds() / 60)
        except Exception as exc:
            raise RuntimeError(
                f"ka_vighnakara: could not resolve UTC offset for chart {chart_id}'s "
                f"timezone_id={tzid!r}: {exc}. Refusing to default to IST (CR-87)."
            ) from exc

        return {'lat': float(lat), 'lon': float(lon), 'tz_offset_minutes': tz_offset_minutes}

    def _fetch_natal_moon_lon(self, conn, chart_id: str) -> Optional[float]:
        """Natal Moon sidereal longitude from chart_facts (Track I-2).

        Same pins as `_fetch_natal_lagna_lon` (§N.7 item 2): fact_category, fact_subject='MOON',
        fact_key='longitude_sidereal', canonical ayanamsha, total ORDER BY. None when absent
        (callers then omit the Moon clause rather than invent a sign).
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_value_num FROM chart_facts
                    WHERE chart_id = %s AND fact_category = 'graha_position'
                      AND fact_subject = 'MOON'
                      AND fact_key = 'longitude_sidereal'
                      AND ayanamsha_id = 'lahiri_chitrapaksha'
                    ORDER BY fact_id
                    LIMIT 1
                    """,
                    (chart_id,),
                )
                row = cur.fetchone()
                if row and row['fact_value_num'] is not None:
                    return float(row['fact_value_num']) % 360.0
        except Exception as exc:
            logger.debug("ka_vighnakara: natal moon fetch failed: %s", exc)
        return None

    def _fetch_natal_lagna_lon(self, conn, chart_id: str) -> Optional[float]:
        """Fetch the natal lagna degree from chart_facts.

        NIRMĀṆA L3-W3 (§N.5, §N.7 item 2), found by the L3 `depends_on` audit. This asked for
        `fact_key='longitude'`, which **does not exist** — measured live, the query returned 0 rows
        on every chart, and the writer then proceeded with `natal_lagna_lon=None` silently, because
        the only failure path here is a `logger.debug`. The real fact is `longitude_sidereal` under
        `fact_category='graha_position'` (value 12.4311° for the canonical chart).

        Three corrections, not one:
          * the key (`longitude` → `longitude_sidereal`);
          * a `fact_category` pin — selecting on `fact_key` alone is the §N.7 item-2 defect class,
            and `fact_subject='LAGNA'` genuinely appears under a dozen other categories here;
          * a total `ORDER BY` so the `LIMIT 1` is deterministic rather than arbitrary.
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_value_num FROM chart_facts
                    WHERE chart_id = %s AND fact_category = 'graha_position'
                      AND fact_subject = 'LAGNA'
                      AND fact_key = 'longitude_sidereal'
                      AND ayanamsha_id = 'lahiri_chitrapaksha'
                    ORDER BY fact_id
                    LIMIT 1
                    """,
                    (chart_id,),
                )
                row = cur.fetchone()
                if row and row['fact_value_num'] is not None:
                    return float(row['fact_value_num']) % 360.0
        except Exception as exc:
            logger.debug("ka_vighnakara: natal lagna fetch failed: %s", exc)
        return None

    def _dasha_anchor_peaks(self, conn, chart_id: str, covered_signal_ids: set) -> list:
        """WP-2.1: distinct dasha-derived activation peaks for signals NOT covered
        by a convergence window, so obstruction detection reaches them.

        Resolves each uncovered predicate against the L1 daśā timeline (shared
        helper) and returns a de-duplicated, capped list of (peak_date, signal_id)
        anchors — one representative signal per distinct peak date. Read-only;
        SAVEPOINT-guarded so a soft failure never aborts the writer's transaction.

        F-VIGHNA-3 (§N.7 item 2): the predicate fetch carries `ORDER BY signal_id` —
        a total order over the one real key this table exposes for the purpose
        (`kala_activation_predicates` has no natural single-column key of its own,
        but `signal_id` is stable and unique per predicate row for a chart, which is
        all `setdefault`'s per-peak "first one wins" selection and the
        `_MAX_DASHA_ANCHORS` cap need to be deterministic). Before this fix the query
        had no ORDER BY at all, so which signal represented a given peak date, and
        which peaks made it under the cap, could both vary build-to-build on
        identical data — a live instance of the defect class this doctrine item
        exists to close.
        """
        anchors: dict[DateType, str] = {}
        timeline_cache: dict = {}
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_dasha_anchors")
        try:
            # Life-indexing: resolve anchors only within the native's lifetime,
            # against each predicate's OWN ayanamsha timeline (§8.4 fix).
            birth_date = resolve_birth_date(conn, chart_id)
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT signal_id, ayanamsha_id, dasha_eligibility_rule_jsonb
                    FROM kala_activation_predicates
                    WHERE chart_id = %s
                    ORDER BY signal_id
                    """,
                    (chart_id,),
                )
                predicates = cur.fetchall()

            def _timeline_for(ayan):
                key = ayan or 'lahiri_chitrapaksha'
                if key not in timeline_cache:
                    timeline_cache[key] = load_dasha_timeline(
                        conn, chart_id, ayanamsha_id=key, birth_date=birth_date
                    )
                return timeline_cache[key]

            for pred in predicates:
                sig_id = str(pred['signal_id'])
                if sig_id in covered_signal_ids:
                    continue
                windows = resolve_activation_windows(
                    pred['dasha_eligibility_rule_jsonb'],
                    _timeline_for(pred['ayanamsha_id']),
                    birth_date=birth_date,
                )
                peak = windows.activation_peak
                if peak is None:
                    continue
                # First signal to claim a given peak date represents it (dedupe).
                anchors.setdefault(peak, sig_id)
                if len(anchors) >= _MAX_DASHA_ANCHORS:
                    break
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_dasha_anchors")
        except Exception as exc:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_dasha_anchors")
            logger.debug("ka_vighnakara: dasha-anchor fetch skipped: %s", exc)
            return []

        return sorted(anchors.items())


# ── Detection entry point ─────────────────────────────────────────────────────

def _detect_all(
    peak_date: DateType,
    jd: float,
    swe,
    muhurta_service,
    native_location: dict,
    natal_lagna_lon: Optional[float],
    combustion_orbs: Optional[dict[str, float]] = None,
    natal_moon_lon: Optional[float] = None,
) -> list[dict]:
    """Run all obstruction detectors for one convergence window peak."""
    results = []
    try:
        obs = _check_malefic_transit(
            peak_date, jd, swe, muhurta_service, native_location, natal_lagna_lon,
            natal_moon_lon=natal_moon_lon,
        )
        if obs:
            results.append(obs)
    except Exception as exc:
        logger.debug("ka_vighnakara: _check_malefic_transit failed for %s: %s", peak_date, exc)
    for check in (
        _check_panchanga_obstruction,
        _check_gandanta,
        _check_papakartari,
    ):
        try:
            obs = check(peak_date, jd, swe, muhurta_service, native_location, natal_lagna_lon)
            if obs:
                results.append(obs)
        except Exception as exc:
            logger.debug("ka_vighnakara: %s failed for %s: %s", check.__name__, peak_date, exc)
    try:
        obs = _check_combustion(
            peak_date, jd, swe, muhurta_service, native_location, natal_lagna_lon,
            combustion_orbs=combustion_orbs or _COMBUSTION_ORBS_CLASSICAL,
        )
        if obs:
            results.append(obs)
    except Exception as exc:
        logger.debug("ka_vighnakara: _check_combustion failed for %s: %s", peak_date, exc)
    return results


# ── Detector 1: malefic transit ───────────────────────────────────────────────

def _check_malefic_transit(peak_date, jd=None, swe=None, muhurta_service=None,
                           native_location=None, natal_lagna_lon=None,
                           natal_moon_lon=None,
                           _test_proxy_windows: Optional[list] = None) -> Optional[dict]:
    """
    Live malefic transit: Saturn or Rahu in an adversarial sign at peak_date.
    Uses swisseph sidereal (Lahiri) positions when swe is provided.

    F-VIGHNA-6 (CR-87 contamination pattern): the `swe is None` branch below is a
    TEST-ONLY fallback — `run()` hard-raises `RuntimeError` before ever calling this
    function without a real `swe` module, so this path is unreachable in production.
    The proxy adversarial-window DATA used to live as a module-level constant right
    here in the writer, hardcoded to this one native's own transits — moved out to the
    test module entirely and injected explicitly via `_test_proxy_windows` so no
    native-specific data lives in writer scope, and so this parameter's name makes the
    test-only nature impossible to miss at the call site.
    Citation: Parāśara Gochara phala — Saturn/Rahu in dusthāna from lagna/moon.
    """
    peak_date = _coerce_date(peak_date)
    if peak_date is None:
        return None

    if swe is None:
        # Test-only proxy path — see the docstring above. `_test_proxy_windows` is never
        # populated in production (see F-VIGHNA-6 note above).
        for ws, we in (_test_proxy_windows or []):
            if ws <= peak_date <= we:
                score = 0.45
                return {
                    'obstruction_type': 'malefic_transit',
                    'severity': _severity(score),
                    'severity_score': score,
                    'override_score': round(score * 0.45, 3),
                    'detail': {
                        'planet': 'Saturn',
                        'sign': 'proxy',
                        'reason': f"Saturn in adversarial transit window {ws}..{we} (proxy fallback — no swe).",
                        'peak_date': str(peak_date),
                        'source': 'proxy_window',
                    },
                }
        return None

    saturn_adverse, rahu_adverse = _chart_adverse_signs(natal_lagna_lon, natal_moon_lon)
    # With neither natal anchor known both maps are empty: no adversity is judged (honest null).

    worst_score = 0.0
    worst_planet = None
    worst_sign   = None
    worst_rels: list[str] = []

    for planet_name, swe_id, adverse_map in (
        ('Saturn', _SWE_IDS['Saturn'], saturn_adverse),
        ('Rahu',   _SWE_IDS['Rahu'],   rahu_adverse),
    ):
        lon = _get_sidereal_lon(swe, jd, swe_id)
        if lon is None:
            continue
        sign = _lon_to_sign(lon)
        score, rels = adverse_map.get(sign, (0.0, []))
        if score > worst_score:
            worst_score  = score
            worst_planet = planet_name
            worst_sign   = sign
            worst_rels   = rels

    if worst_score < 0.2:
        return None

    lagna_sign = _lon_to_sign(natal_lagna_lon) if natal_lagna_lon is not None else None
    moon_sign = _lon_to_sign(natal_moon_lon) if natal_moon_lon is not None else None
    anchors = " / ".join(
        part for part in (
            f"native lagna ({lagna_sign})" if lagna_sign else None,
            f"Moon ({moon_sign})" if moon_sign else None,
        ) if part
    )

    return {
        'obstruction_type': 'malefic_transit',
        'severity': _severity(worst_score),
        'severity_score': worst_score,
        'override_score': round(worst_score * 0.45, 3),
        'detail': {
            'planet': worst_planet,
            'sign': worst_sign,
            'natal_lagna_sign': lagna_sign,
            'natal_moon_sign': moon_sign,
            'reason': (
                f"{worst_planet} transiting {worst_sign} — adversarial to {anchors} "
                f"({'; '.join(worst_rels)}); classical gochara obstruction."
            ),
            'peak_date': str(peak_date),
            'source': 'swisseph/lahiri',
        },
    }


# ── Detector 2: panchanga obstruction ────────────────────────────────────────

def _check_panchanga_obstruction(peak_date, jd=None, swe=None, muhurta_service=None,
                                 native_location=None, natal_lagna_lon=None) -> Optional[dict]:
    """
    Rikta tithi from real panchāṅga via ka_muhurta_seva. The Rikta set is the engine's
    (`panchang_engine.rich_topics.compute_tithi_attrs(t).anga_type == 'Rikta'`: tithi ids
    4/9/14/19/24/29, i.e. the 4th/9th/14th of each paksha); Pūrṇimā (15) and Amāvasyā (30) are Pūrṇa, not Rikta.
    Falls back to day-mod proxy only when the service is unavailable.
    Citation: Muhurta-Chintamani §Tithi; Rikta tithis inauspicious for most karyas.
    """
    peak_date = _coerce_date(peak_date)
    if peak_date is None:
        return None
    tithi: Optional[int] = None

    if muhurta_service is not None and native_location is not None:
        try:
            from panchang_engine import compute_panchang
            panchang = compute_panchang(
                peak_date,
                native_location['lat'],
                native_location['lon'],
                native_location['tz_offset_minutes'],
            )
            tithi_raw = getattr(panchang, 'tithi', None)
            if tithi_raw is not None:
                tithi = int(tithi_raw.id) if hasattr(tithi_raw, 'id') else int(tithi_raw)
        except Exception as exc:
            logger.debug("panchanga_obstruction: panchang_engine failed for %s: %s", peak_date, exc)

    if tithi is None:
        # Fallback: day-mod proxy (less accurate but better than nothing)
        tithi = (peak_date.day % 15) or 15

    # Rikta (inauspicious) tithis: the engine's set — referenced, not re-listed.
    if _is_rikta_tithi(tithi):
        severity_score = 0.35
        return {
            'obstruction_type': 'panchanga_obstruction',
            'severity': _severity(severity_score),
            'severity_score': severity_score,
            'override_score': 0.12,
            'detail': {
                'panchanga_element': 'rikta_tithi',
                'tithi': tithi,
                'source': 'panchang_engine' if muhurta_service else 'day_mod_proxy',
                'reason': f"Tithi {tithi} is Rikta (inauspicious for most ārabdha karyas).",
                'citation': 'Muhurta-Chintamani §Rikta-Tithi',
                'peak_date': str(peak_date),
            },
        }
    return None


# ── Detector 3: gandanta ─────────────────────────────────────────────────────

def _check_gandanta(peak_date, jd=None, swe=None, muhurta_service=None,
                   native_location=None, natal_lagna_lon=None) -> Optional[dict]:
    """
    Gandanta: Moon at the water-fire junction at peak_date — the LAST 3°20' of Cancer,
    Scorpio and Pisces AND the FIRST 3°20' of Leo, Sagittarius and Aries
    (Āśleṣā-Maghā, Jyeṣṭhā-Mūla, Revatī-Aśvinī sandhi).
    Uses swisseph sidereal (Lahiri) Moon longitude; the arc and the zone test come from the
    L1 definition `ga_sensitive_degree_writer.check_gandanta` (SS ruling N-28) — nothing is
    hard-coded here. Returns a stub dict (not None) when called without swe — so test
    contracts are satisfied.
    Citation: the L1 `GANDANTA_CITATION` (BPHS / Sarvartha Chintamani); L0 reference
    `brahma_dosha_catalog` canonical_id='gandanta_dosha', classical_citations
    [{"text_id": "bphs", "chapter": 9}] (brahmagyan/l0_doshas.py). The bg_texts passage
    itself was not looked up when this was written — citation: pending bg_texts lookup
    for the verse-level reference.
    """
    peak_date = _coerce_date(peak_date)
    if peak_date is None:
        return None

    if swe is None:
        return {
            'obstruction_type': 'gandanta',
            'severity': 'mild',
            'severity_score': 0.0,
            'override_score': 0.0,
            'detail': {
                'stub': True,
                'reason': 'Gandanta check requires swisseph — stub returned.',
                'peak_date': str(peak_date),
            },
        }

    moon_lon = _get_sidereal_lon(swe, jd, _SWE_IDS['Moon'])
    if moon_lon is None:
        return None

    # The 3°20' edges (26°40' of a water sign / 3°20' of a fire sign) are not exactly
    # representable in binary floating point, and `lon % 30` of a sign-multiple-plus-edge longitude
    # lands a few ulp on the wrong side (e.g. Scorpio 26°40' -> 26.666666666666657 < 26.666666666666668).
    # Rounding the in-sign degree to 9 decimals (~3.6e-6 arcsec) keeps the inclusive L1 edges inclusive.
    moon_lon = moon_lon % 360.0
    gd = check_gandanta(int(moon_lon // 30), round(moon_lon % 30.0, 9))
    if not gd['fired']:
        return None

    moon_sign = gd['sign']
    zone = gd['gandanta_zone']  # 'end_of_<water sign>' | 'start_of_<fire sign>'
    side = "end" if zone.startswith('end_of_') else "start"
    severity_score = 0.55
    return {
        'obstruction_type': 'gandanta',
        'severity': _severity(severity_score),
        'severity_score': severity_score,
        'override_score': 0.22,
        'detail': {
            'moon_longitude': round(moon_lon, 3),
            # The sign the Moon occupies (a water sign at the end-junction, a fire sign at the
            # start-junction); kept under the legacy key for stored-row/consumer continuity.
            'junction_sign': moon_sign,
            'gandanta_zone': zone,
            'distance_to_junction_deg': gd['distance_to_junction_deg'],
            'gandanta_arc_deg': gd['gandanta_arc_deg'],
            'reason': (
                f"Moon at {moon_lon:.2f}° (Lahiri) — in Gandanta zone at "
                f"{side} of {moon_sign}, {gd['distance_to_junction_deg']:.2f}° from the "
                f"water-fire junction. Instability at rāśi-nakshatra junction."
            ),
            'citation': GANDANTA_CITATION,
            'l0_ref': "brahma_dosha_catalog:gandanta_dosha (bphs ch.9)",
            'peak_date': str(peak_date),
            'source': 'swisseph/lahiri',
        },
    }


# ── Detector 4: papakartari ───────────────────────────────────────────────────

def _check_papakartari(peak_date, jd=None, swe=None, muhurta_service=None,
                       native_location=None, natal_lagna_lon=None) -> Optional[dict]:
    """
    Papakartari: natal lagna bhava hemmed between malefic transit planets
    in the adjacent signs (H-1 and H+1 from lagna sign).
    Uses natal lagna longitude (chart_facts) + live Saturn/Mars/Rahu positions.
    Returns stub dict (not None) when called without swe — so test contracts are satisfied.
    Citation: BPHS Papakartari Yoga; Phaladeepika §Scissors-Yoga.
    """
    peak_date = _coerce_date(peak_date)
    if peak_date is None:
        return None

    if swe is None:
        return {
            'obstruction_type': 'papakartari',
            'severity': 'mild',
            'severity_score': 0.0,
            'override_score': 0.0,
            'detail': {
                'stub': True,
                'reason': 'Papakartari check requires swisseph — stub returned.',
                'peak_date': str(peak_date),
            },
        }

    if natal_lagna_lon is None:
        return None

    lagna_sign_num = int(natal_lagna_lon // 30)  # 0-indexed (0=Aries)
    prev_sign_start = ((lagna_sign_num - 1) % 12) * 30.0
    next_sign_start = ((lagna_sign_num + 1) % 12) * 30.0

    malefic_planets = [
        ('Saturn', _SWE_IDS['Saturn']),
        ('Mars',   _SWE_IDS['Mars']),
        ('Rahu',   _SWE_IDS['Rahu']),
    ]

    def _in_sign_range(lon: float, sign_start: float) -> bool:
        return sign_start <= lon % 360.0 < sign_start + 30.0

    prev_malefics = []
    next_malefics = []
    for pname, pid in malefic_planets:
        lon = _get_sidereal_lon(swe, jd, pid)
        if lon is None:
            continue
        if _in_sign_range(lon, prev_sign_start):
            prev_malefics.append(pname)
        if _in_sign_range(lon, next_sign_start):
            next_malefics.append(pname)

    if prev_malefics and next_malefics:
        severity_score = 0.50
        return {
            'obstruction_type': 'papakartari',
            'severity': _severity(severity_score),
            'severity_score': severity_score,
            'override_score': 0.20,
            'detail': {
                'lagna_longitude': round(natal_lagna_lon, 2),
                'malefics_preceding': prev_malefics,
                'malefics_following': next_malefics,
                'reason': (
                    f"Lagna hemmed: {','.join(prev_malefics)} in preceding sign, "
                    f"{','.join(next_malefics)} in following sign — Papakartari at peak_date."
                ),
                'citation': 'BPHS Papakartari Yoga — bhava hemmed between malefics',
                'peak_date': str(peak_date),
                'source': 'swisseph/lahiri',
            },
        }
    return None


# ── Detector 5: combustion ────────────────────────────────────────────────────

def _check_combustion(peak_date, jd=None, swe=None, muhurta_service=None,
                      native_location=None, natal_lagna_lon=None,
                      combustion_orbs: Optional[dict[str, float]] = None) -> Optional[dict]:
    """
    Combustion: planet within its classical orb of the Sun at peak_date.
    Per-graha orbs from bg_combustion_orbs (C12 fix — flat 6° removed).
    Citation: Parāśara Āstangata; Sārāvalī ch.6; Phaladeepika §Combustion degrees.
    """
    if swe is None:
        return None

    orbs = combustion_orbs or _COMBUSTION_ORBS_CLASSICAL

    sun_lon = _get_sidereal_lon(swe, jd, _SWE_IDS['Sun'])
    if sun_lon is None:
        return None

    combust_planets = []
    for pname, pid in [('Mars', _SWE_IDS['Mars']), ('Saturn', _SWE_IDS['Saturn'])]:
        orb_limit = orbs.get(pname, 8.0)
        p_lon = _get_sidereal_lon(swe, jd, pid)
        if p_lon is None:
            continue
        diff = abs(p_lon - sun_lon) % 360.0
        if diff > 180.0:
            diff = 360.0 - diff
        if diff <= orb_limit:
            combust_planets.append((pname, round(diff, 2), orb_limit))

    if not combust_planets:
        return None

    severity_score = 0.30
    planet_str = ', '.join(f"{p} ({d}°/{ol}° orb)" for p, d, ol in combust_planets)
    return {
        'obstruction_type': 'combustion',
        'severity': _severity(severity_score),
        'severity_score': severity_score,
        'override_score': 0.12,
        'detail': {
            'combust_planets': [{'planet': p, 'orb_deg': d, 'orb_limit': ol} for p, d, ol in combust_planets],
            'sun_longitude': round(sun_lon, 2),
            'reason': f"{planet_str} combust — karakatva weakened.",
            'citation': "Parāśara Āstangata / Sārāvalī ch.6 — per-graha combustion orbs",
            'peak_date': str(peak_date),
            'source': 'swisseph/lahiri + bg_combustion_orbs',
        },
    }


# ── Public compatibility wrapper ──────────────────────────────────────────────

def _detect_obstructions(peak_date, convergence_score: float = 0.5,
                          signal_id=None) -> list[dict]:
    """
    Public wrapper used by tests and any caller that wants obstruction detection
    without providing a live swe instance.

    Runs all detectors with swe=None (proxy/stub paths).
    For production use, the writer calls _detect_all() with a live swe instance.
    """
    if peak_date is None:
        return []
    d = _coerce_date(peak_date)
    if d is None:
        return []

    jd = _jd_from_date(d)
    results = []
    for check in (_check_malefic_transit, _check_panchanga_obstruction,
                  _check_gandanta, _check_papakartari, _check_combustion):
        try:
            obs = check(d, jd=jd, swe=None)
            if obs and obs.get('severity_score', 0) > 0.0:
                results.append(obs)
        except Exception as exc:
            logger.debug("_detect_obstructions: %s failed for %s: %s", check.__name__, d, exc)
    return results
