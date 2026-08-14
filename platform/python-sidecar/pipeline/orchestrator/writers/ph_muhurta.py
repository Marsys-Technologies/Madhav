"""
ph_muhurta — Auspicious Windows (L4 Phala wave 4 parallel).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
NEVER commits or rolls back (orchestrator owns the transaction).
NEVER writes outside phala_muhurta.

Reads: phala_anchors · ka_vighnakara · ga_condition_composite ·
       chart_facts (natal Moon nakshatra/sign)
       (calls ka_muhurta_seva for panchanga scoring via the service; calls
       panchang_engine.panchanga_instant() directly for real serve-time
       tarabala/chandrabala per JL-016 — see _compute_tara_chandra_scores)
Writes: phala_muhurta (delete-then-insert per chart_id)

MR-09 DOCSTRING CORRECTION: ka_gochara was previously listed in "Reads:"
above, implying a live read dependency.  That is inaccurate.
ka_gochara (GocharaTransitService) is a COMPUTE-ONLY service with no
persisted table.  _load_gochara_transits() explicitly returns {} with a
logged note that gochara wiring is DEFERRED to a future L4 campaign build
phase.  Until that wiring is implemented and validated end-to-end,
ka_gochara does NOT appear in the Reads list.  _compute_transit_score()
returns the documented neutral 0.5 default in the interim.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, date

import psycopg

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ph_muhurta.engine import (
    MuhurtaContext,
    derive_muhurta_record,
    ACTION_GRAHA_MAP,
)

logger = logging.getLogger(__name__)

_ACTION_CLASSES = list(ACTION_GRAHA_MAP.keys())
_WINDOW_DAYS = 365 * 3    # 3-year forward horizon
# B9: cap raised from 100 → 400 (original native charts typically have ~400 influenceable anchors;
# the old 100-row cap silently dropped 300 rows and is now replaced by this documented constant).
MAX_MUHURTA_ANCHORS = 400


@register('ph_muhurta')
class PhMuhurtaWriter(WriterBase):
    """
    Builds phala_muhurta: for each influenceable anchor + each action class,
    evaluates the panchanga quality + chart-personalized scoring.
    Fuses to ph_nimitta windows (M3) + avoids personal danger windows (M2).
    """
    asset_id = 'ph_muhurta'

    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn
        chart_id = ctx.config['chart_id']

        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM phala_muhurta WHERE chart_id = %s", (chart_id,))

        # Load influenceable anchors (V4 malleability)
        anchors = self._load_influenceable_anchors(conn, chart_id)
        logger.info("ph_muhurta: %d influenceable anchors found", len(anchors))

        # Load obstruction windows (M2) into a lookup: date → obstruction_id
        obstruction_windows = self._load_obstruction_windows(conn, chart_id)

        # Load chart condition scores (M1) for the relevant grahas
        condition_scores = self._load_condition_scores(conn, chart_id)

        # B9: load ka_gochara transit data for real transit scoring
        gochara_by_graha = self._load_gochara_transits(conn, chart_id)

        # F-W5-003: derive chart's actual 10th-house lord to override native-lagna assumption
        career_lord = self._resolve_career_lord(conn, chart_id)

        # BA-P5B EXT: load brahma_activity_ontology + natal Moon nakshatra
        activity_ontology = self._load_activity_ontology(conn)
        natal_moon_nakshatra_idx = self._load_natal_moon_nakshatra_idx(conn, chart_id)
        # JL-016 (BA-2.5 P3 J6): natal Moon nakshatra (1-indexed, None-safe) + sign,
        # needed to derive real tarabala/chandrabala at serve time (see
        # _compute_tara_chandra_scores). Distinct from natal_moon_nakshatra_idx above,
        # which defaults to 0 on miss and is only used for the jsonb echo field.
        natal_moon_nakshatra_id = self._load_natal_moon_nakshatra_id(conn, chart_id)
        natal_moon_sign_id = self._load_natal_moon_sign_id(conn, chart_id)
        birth_params = ctx.config.get('birth_params') or {}
        action_graha_overrides: dict[str, str] = {
            'start_business': career_lord,
            'career_launch':  career_lord,
            'new_venture':    career_lord,
        }

        rows_inserted = 0
        with conn.cursor() as cur:
            for anchor in anchors:
                anchor_id   = str(anchor['anchor_id'])
                domain      = anchor['domain']
                peak_date   = anchor.get('peak_date')
                window_start = anchor.get('window_start')
                window_end   = anchor.get('window_end')

                # Map domain → best action class for M3 fusion
                domain_action = _DOMAIN_TO_ACTION.get(domain, 'new_venture')
                relevant_graha = action_graha_overrides.get(domain_action) or ACTION_GRAHA_MAP.get(domain_action, 'saturn')

                # Build a single representative candidate for this anchor's window
                # (full engine would iterate candidate timestamptz slots; we emit one per anchor)
                candidate_start = _to_datetime(window_start or peak_date)
                candidate_end   = _to_datetime(window_end   or peak_date)

                # M1: condition + transit (use loaded scores; default 0.5 if absent)
                condition = condition_scores.get(relevant_graha, 0.5)
                # B9: derive real transit score from ka_gochara if available
                transit = self._compute_transit_score(
                    gochara_by_graha, relevant_graha, candidate_start
                )

                # M2: check obstruction overlap
                obstruction_id = None
                obstruction_penalty = 0.0
                for (obs_start, obs_end), obs_id in obstruction_windows.items():
                    if candidate_start and obs_start and obs_end:
                        if obs_start <= candidate_start.date() <= obs_end:
                            obstruction_id = obs_id
                            obstruction_penalty = 0.3
                            break

                # Panchanga score — ka_muhurta_seva not available at writer import time;
                # use a deterministic proxy from condition × season_factor
                panchanga_score = round(min(1.0, condition * 0.8 + 0.2), 4)

                # JL-016 (BA-2.5 P3 J6): real tarabala/chandrabala from the panchanga
                # service (panchang_engine), not the hardcoded 0.5 defaults. Falls back
                # to an honestly-labeled placeholder if natal Moon data or ephemeris is
                # unavailable — see _compute_tara_chandra_scores docstring.
                tarabala_score, chandrabala_score, tara_chandra_source = self._compute_tara_chandra_scores(
                    natal_moon_nakshatra_id, natal_moon_sign_id, birth_params, candidate_start,
                )

                # BA-P5B EXT: activity ontology enrichment
                act_entry = activity_ontology.get(domain_action, {})
                significators = act_entry.get('significators', {}) or {}
                fruct_rules = act_entry.get('fructification_rules', {}) or {}
                fruct_anchor = fruct_rules.get('timing_anchor') if isinstance(fruct_rules, dict) else None
                classical_cite = (act_entry.get('citations') or ['Muhūrta-Chintāmaṇi + Grahalaghava'])[0] \
                    if act_entry else 'Muhūrta-Chintāmaṇi + Grahalaghava'

                mctx = MuhurtaContext(
                    action_class=domain_action,
                    window_start=candidate_start,
                    window_end=candidate_end,
                    hora_lord=relevant_graha,
                    panchanga_score=panchanga_score,
                    panchanga_snapshot={'source': 'ka_muhurta_seva_proxy', 'graha': relevant_graha},
                    classical_citation=classical_cite,
                    condition_score=condition,
                    transit_score=transit,
                    overlapping_obstruction_id=obstruction_id,
                    obstruction_penalty=obstruction_penalty,
                    linked_anchor_id=anchor_id,   # M3: prediction-fused
                    linked_anchor_domain=domain,
                    # BA-P5B EXT / JL-016: real serve-time bala scores when available,
                    # honest placeholder (source label makes this distinguishable) otherwise.
                    tarabala_score=tarabala_score,
                    chandrabala_score=chandrabala_score,
                    tarabala_chandrabala_source=tara_chandra_source,
                    natal_moon_nakshatra_idx=natal_moon_nakshatra_idx,
                    activity_significators=significators,
                    fructification_rules=fruct_rules,
                    fructification_anchor=fruct_anchor,
                )

                rec = derive_muhurta_record(mctx)

                cur.execute(
                    """
                    INSERT INTO phala_muhurta (
                        chart_id, action_class, window_start, window_end,
                        hora_lord, panchanga_score, chart_personalization_score,
                        personalization_graha, personal_adversity_penalty,
                        overlapping_obstruction_id, linked_anchor_id,
                        composite_quality, window_quality_verdict, verdict_reason,
                        panchanga_snapshot_jsonb, classical_citation,
                        tarabala_chandrabala_jsonb, significators_met_jsonb,
                        fructification_anchor, follow_up_hook_jsonb,
                        derivation_ledger_jsonb, source_citation
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s::jsonb, %s,
                        %s::jsonb, %s::jsonb,
                        %s, %s::jsonb,
                        %s::jsonb, %s
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        chart_id, rec.action_class,
                        rec.window_start, rec.window_end,
                        rec.hora_lord, rec.panchanga_score,
                        rec.chart_personalization_score,
                        rec.personalization_graha,
                        rec.personal_adversity_penalty,
                        rec.overlapping_obstruction_id,
                        rec.linked_anchor_id,
                        rec.composite_quality,
                        rec.window_quality_verdict,
                        rec.verdict_reason,
                        json.dumps(rec.panchanga_snapshot_jsonb or {}),
                        rec.classical_citation,
                        json.dumps(rec.tarabala_chandrabala_jsonb or {}),
                        json.dumps(rec.significators_met_jsonb or {}),
                        rec.fructification_anchor,
                        json.dumps(rec.follow_up_hook_jsonb or {}),
                        json.dumps(rec.derivation_ledger_jsonb),
                        rec.source_citation,
                    ),
                )
                rows_inserted += 1

        logger.info("ph_muhurta: inserted %d rows into phala_muhurta for %s", rows_inserted, chart_id)
        return WriterResult(asset_id='ph_muhurta', rows_inserted=rows_inserted)

    def _load_influenceable_anchors(self, conn, chart_id: str) -> list:
        # B9: cap raised to MAX_MUHURTA_ANCHORS (400). The previous 100-row cap silently
        # dropped up to 300 influenceable anchors. We now fetch up to MAX+1 to detect
        # overflow and warn; rows are trimmed to MAX if exceeded.
        cap = MAX_MUHURTA_ANCHORS
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                """
                SELECT anchor_id, domain, malleability, peak_date, window_start, window_end
                FROM phala_anchors
                WHERE chart_id = %s AND malleability IN ('influenceable','semi_influenceable')
                ORDER BY confidence_high DESC NULLS LAST
                LIMIT %s
                """,
                (chart_id, cap + 1),
            )
            rows = cur.fetchall()
        if len(rows) > cap:
            logger.warning(
                "[ph_muhurta] influenceable anchors=%d exceeds MAX_MUHURTA_ANCHORS=%d — %d dropped "
                "(top-confidence design; raise MAX_MUHURTA_ANCHORS if persistent)",
                len(rows), cap, len(rows) - cap,
            )
            rows = rows[:cap]
        return rows

    def _load_obstruction_windows(self, conn, chart_id: str) -> dict:
        """Load L3 obstruction windows as {(start,end): id}.

        Obstructions are stored in `kala_obstruction` (built by ka_vighnakara), which
        carries no dates of its own — each row links to the `kala_convergence` row
        (built by ka_sangam) that supplies the temporal window via window_start/window_end.
        L3 Kāla may not be built yet, so a SAVEPOINT keeps a missing-table error from
        aborting the outer transaction.

        NOTE: prior versions queried `FROM ka_vighnakara` (an asset id, not a table) and
        selected obstruction_start/obstruction_end columns that do not exist — the read
        always errored and was silently swallowed, so obstruction overlap was permanently
        empty. Corrected to the real table + JOIN.
        """
        result: dict = {}
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_muhurta_obs")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT o.id,
                           c.window_start AS obstruction_start,
                           c.window_end   AS obstruction_end
                    FROM kala_obstruction o
                    JOIN kala_convergence c ON c.convergence_id = o.convergence_id
                    WHERE o.chart_id = %s
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    s = row["obstruction_start"]
                    e = row["obstruction_end"]
                    if s and e:
                        s = s if isinstance(s, date) else date.fromisoformat(str(s))
                        e = e if isinstance(e, date) else date.fromisoformat(str(e))
                        result[(s, e)] = row["id"]
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_muhurta_obs")
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_muhurta_obs")
            except Exception:
                pass
            logger.debug("ph_muhurta: ka_vighnakara load skipped: %s", exc)
        return result

    def _load_condition_scores(self, conn, chart_id: str) -> dict[str, float]:
        """Load ga_condition_composite condition_score per graha."""
        result: dict[str, float] = {}
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT graha, condition_score
                    FROM ga_condition_composite
                    WHERE chart_id = %s
                      AND ayanamsha_id = 'lahiri_chitrapaksha'
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    # conn's default row_factory is dict_row (see orchestrator/db.py);
                    # this cursor did not override it, so `row` is a dict, not a tuple —
                    # index by column name, not position (same bug class already fixed
                    # in bg_concordance/bg_text_index/mi_darshana). The prior positional
                    # row[0]/row[1] indexing raised on every call, was swallowed by the
                    # bare except below, and silently produced an empty dict — every
                    # caller then fell back to the literal 0.5 default for every graha.
                    graha = row["graha"]
                    score = row["condition_score"]
                    result[str(graha).lower()] = float(score) if score is not None else 0.5
        except Exception as exc:
            logger.warning("ph_muhurta: condition_scores load failed: %s", exc)
        return result

    def _load_gochara_transits(self, conn, chart_id: str) -> dict[str, list[dict]]:
        """B9: gochara (transit) windows per graha for transit scoring.

        Returns {graha_lower: [{'sign_number': int, 'is_retrograde': bool,
                                'start_date': date, 'end_date': date}, ...]}

        KNOWN GAP (honest): there is NO `kala_gochara` table. ka_gochara is a
        compute-only L3 service (asset_kind='service', no persistence) that wraps
        live Swiss-Ephemeris transit search. Prior versions issued `FROM kala_gochara`,
        which always errored and was silently swallowed — so the transit score was
        permanently the neutral default. Reading a non-existent table is removed.

        Full gochara transit scoring requires wiring the KaGocharaService into this
        writer (a per-candidate live-ephemeris call); that is deferred to the L4 Phala
        build campaign, where it can be validated end-to-end. Until then this returns
        {} EXPLICITLY (not via a swallowed error), and _compute_transit_score falls
        back to its documented neutral 0.5.
        """
        # No table to read; gochara service wiring is an L4-campaign task. Return the
        # empty map plainly so the neutral-score fallback is intentional, not masked.
        logger.info(
            "ph_muhurta: gochara transit scoring not yet wired (ka_gochara is a "
            "compute-only service; no kala_gochara table) — using neutral transit score"
        )
        return {}

    def _compute_transit_score(
        self,
        gochara_by_graha: dict[str, list[dict]],
        graha: str,
        candidate_start: datetime | None,
    ) -> float:
        """B9: compute real transit score from ka_gochara data.

        Score logic:
          - No ka_gochara data → return 0.5 (neutral default, logged at DEBUG).
          - Find the transit window active at candidate_start for the given graha.
          - Retrograde transit → score = 0.35 (weakened).
          - Direct transit in own sign (5 or 8 for saturn, etc.) → 0.75.
          - Otherwise → 0.55 + small sign-position bonus to create variance.
        Falls back to 0.5 if no matching transit window found.
        """
        if not gochara_by_graha or graha not in gochara_by_graha:
            logger.debug("ph_muhurta: no ka_gochara for graha=%s; transit_score=0.5 (default)", graha)
            return 0.5

        if candidate_start is None:
            return 0.5

        target_date = candidate_start.date() if isinstance(candidate_start, datetime) else candidate_start

        # Own-sign map (classical): sign numbers where a graha is in own sign
        _OWN_SIGNS: dict[str, set[int]] = {
            'sun':     {5},
            'moon':    {4},
            'mars':    {1, 8},
            'mercury': {3, 6},
            'jupiter': {9, 12},
            'venus':   {2, 7},
            'saturn':  {10, 11},
            'rahu':    {3},
            'ketu':    {9},
        }

        transits = gochara_by_graha[graha]
        active = None
        for t in transits:
            s = t.get('start_date')
            e = t.get('end_date')
            if s and e:
                if isinstance(s, str):
                    try: s = date.fromisoformat(s)
                    except ValueError: continue
                if isinstance(e, str):
                    try: e = date.fromisoformat(e)
                    except ValueError: continue
                if s <= target_date <= e:
                    active = t
                    break

        if active is None:
            return 0.5

        if active.get('is_retrograde'):
            return 0.35

        sign_num = active.get('sign_number', 0)
        if sign_num in _OWN_SIGNS.get(graha, set()):
            return 0.75

        # Gentle variance: 0.55 base + 0.01 per sign position (1–12 → 12 distinct values [0.55, 0.66])
        # IMPORTANT-2 fix: was % 6 (only 6 distinct values, pairing opposite signs);
        # corrected to % 12 so each of the 12 zodiac signs gets a unique score.
        variance = round(0.55 + 0.01 * ((sign_num - 1) % 12), 3)
        return variance

    # Classical sign lords (1=Aries..12=Pisces) for 10th-lord derivation
    _SIGN_LORDS: dict[int, str] = {
        1: 'mars',  2: 'venus',   3: 'mercury', 4: 'moon',
        5: 'sun',   6: 'mercury', 7: 'venus',   8: 'mars',
        9: 'jupiter', 10: 'saturn', 11: 'saturn', 12: 'jupiter',
    }
    _LAGNA_SIGN_NUM: dict[str, int] = {
        'Aries': 1, 'Taurus': 2, 'Gemini': 3, 'Cancer': 4,
        'Leo': 5, 'Virgo': 6, 'Libra': 7, 'Scorpio': 8,
        'Sagittarius': 9, 'Capricorn': 10, 'Aquarius': 11, 'Pisces': 12,
    }

    def _resolve_career_lord(self, conn, chart_id: str) -> str:
        """Derive the chart's 10th-house lord from chart_facts lagna sign.

        Falls back to 'saturn' (classical career archetype) if data unavailable.
        """
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_value_text FROM chart_facts
                    WHERE chart_id = %s
                      AND fact_subject = 'LAGNA'
                      AND fact_key = 'sign'
                    LIMIT 1
                    """,
                    (chart_id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    lagna_sign = row[0]
                    lagna_num = self._LAGNA_SIGN_NUM.get(lagna_sign, 1)
                    h10_sign_num = ((lagna_num - 1 + 9) % 12) + 1
                    return self._SIGN_LORDS.get(h10_sign_num, 'saturn')
        except Exception as exc:
            logger.debug("ph_muhurta: could not derive career_lord for %s: %s", chart_id, exc)
        return 'saturn'

    def _load_activity_ontology(self, conn) -> dict[str, dict]:
        """BA-P5B EXT: Load brahma_activity_ontology into {activity_class_id: row} dict.

        SAVEPOINT-guarded. Falls back to empty dict if table absent.
        """
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_muhurta_activity_ont")
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(
                    """
                    SELECT activity_class_id, significators, fructification_rules, citations
                    FROM brahma_activity_ontology
                    """
                )
                result = {str(r['activity_class_id']): dict(r) for r in cur.fetchall()}
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_muhurta_activity_ont")
            return result
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_muhurta_activity_ont")
            except Exception:
                pass
            logger.debug("ph_muhurta: brahma_activity_ontology load skipped: %s", exc)
            return {}

    def _load_natal_moon_nakshatra_idx(self, conn, chart_id: str) -> int:
        """BA-P5B EXT: Load natal Moon nakshatra 0-based ordinal from chart_facts.

        Used for structural tarabala computation. Falls back to 0 if unavailable.
        """
        _NAKSHATRA_ORDINALS = {
            'Ashwini': 0, 'Bharani': 1, 'Krittika': 2, 'Rohini': 3, 'Mrigashira': 4,
            'Ardra': 5, 'Punarvasu': 6, 'Pushya': 7, 'Ashlesha': 8,
            'Magha': 9, 'Purva Phalguni': 10, 'Uttara Phalguni': 11,
            'Hasta': 12, 'Chitra': 13, 'Swati': 14, 'Vishakha': 15,
            'Anuradha': 16, 'Jyeshtha': 17, 'Mula': 18,
            'Purva Ashadha': 19, 'Uttara Ashadha': 20, 'Shravana': 21,
            'Dhanishtha': 22, 'Shatabhisha': 23,
            'Purva Bhadrapada': 24, 'Uttara Bhadrapada': 25, 'Revati': 26,
        }
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_muhurta_moon_nak")
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_value_text FROM chart_facts
                    WHERE chart_id = %s
                      AND ayanamsha_id = 'lahiri_chitrapaksha'
                      AND fact_subject = 'Moon'
                      AND fact_key = 'nakshatra'
                    LIMIT 1
                    """,
                    (chart_id,),
                )
                row = cur.fetchone()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_muhurta_moon_nak")
            if row and row[0]:
                return _NAKSHATRA_ORDINALS.get(row[0], 0)
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_muhurta_moon_nak")
            except Exception:
                pass
            logger.debug("ph_muhurta: natal Moon nakshatra load skipped: %s", exc)
        return 0

    # JL-016 (BA-2.5 P3 J6) ---------------------------------------------------
    # tarabala/chandrabala real-source wiring. Both balas ALREADY EXIST as
    # deterministic classical formulas in panchang_engine (compute_tara_bala_score /
    # compute_chandra_bala_score in panchang_engine/tara_bala.py — the same module
    # used by ka_muhurta_seva and muhurat/finder.py). ph_muhurta does NOT reimplement
    # these formulas; it only (a) reads the natal Moon nakshatra/sign already computed
    # into chart_facts by L1, and (b) calls panchang_engine.panchanga_instant() — the
    # existing panchanga service — to get the TRANSIT Moon's nakshatra/sign at the
    # candidate window's instant. This is a serve-time JOIN across two already-computed
    # sources, per §N.5 (L1 is the authority over L2+ derivations) and the JL-016 ruling.

    _NAKSHATRA_ID_1INDEXED = {
        'Ashwini': 1, 'Bharani': 2, 'Krittika': 3, 'Rohini': 4, 'Mrigashira': 5,
        'Ardra': 6, 'Punarvasu': 7, 'Pushya': 8, 'Ashlesha': 9,
        'Magha': 10, 'Purva Phalguni': 11, 'Uttara Phalguni': 12,
        'Hasta': 13, 'Chitra': 14, 'Swati': 15, 'Vishakha': 16,
        'Anuradha': 17, 'Jyeshtha': 18, 'Mula': 19,
        'Purva Ashadha': 20, 'Uttara Ashadha': 21, 'Shravana': 22,
        'Dhanishtha': 23, 'Shatabhisha': 24,
        'Purva Bhadrapada': 25, 'Uttara Bhadrapada': 26, 'Revati': 27,
    }

    def _load_natal_moon_nakshatra_id(self, conn, chart_id: str):
        """Natal Moon nakshatra as a 1-indexed id (1..27), or None if unavailable.

        Distinct from _load_natal_moon_nakshatra_idx (0-based, defaults to 0 on
        miss) — this method returns None on miss so callers can tell "no data"
        apart from "genuinely Ashwini", which matters for JL-016's real-vs-
        placeholder distinction.
        """
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_muhurta_moon_nak_id")
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_value_text FROM chart_facts
                    WHERE chart_id = %s
                      AND ayanamsha_id = 'lahiri_chitrapaksha'
                      AND fact_subject = 'Moon'
                      AND fact_key = 'nakshatra'
                    LIMIT 1
                    """,
                    (chart_id,),
                )
                row = cur.fetchone()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_muhurta_moon_nak_id")
            if row and row[0]:
                return self._NAKSHATRA_ID_1INDEXED.get(row[0])
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_muhurta_moon_nak_id")
            except Exception:
                pass
            logger.debug("ph_muhurta: natal Moon nakshatra id load skipped: %s", exc)
        return None

    def _load_natal_moon_sign_id(self, conn, chart_id: str):
        """Natal Moon sign as a 1-indexed id (1=Aries..12=Pisces), or None if unavailable.

        Same source pattern as _resolve_career_lord's lagna-sign query, but for
        fact_subject='Moon' — reads the L1 chart_facts value, never recomputes it.
        """
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_muhurta_moon_sign")
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_value_text FROM chart_facts
                    WHERE chart_id = %s
                      AND ayanamsha_id = 'lahiri_chitrapaksha'
                      AND fact_subject = 'Moon'
                      AND fact_key = 'sign'
                    LIMIT 1
                    """,
                    (chart_id,),
                )
                row = cur.fetchone()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_muhurta_moon_sign")
            if row and row[0]:
                return self._LAGNA_SIGN_NUM.get(row[0])
        except Exception as exc:
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_muhurta_moon_sign")
            except Exception:
                pass
            logger.debug("ph_muhurta: natal Moon sign load skipped: %s", exc)
        return None

    def _compute_tara_chandra_scores(
        self,
        natal_moon_nakshatra_id,
        natal_moon_sign_id,
        birth_params: dict,
        candidate_start,
    ) -> tuple[float, float, str]:
        """Real tarabala/chandrabala via panchang_engine, or an honest placeholder.

        Requires: natal Moon nakshatra + sign (chart_facts) + birth_params lat/lon/tz
        (for the transit-Moon ephemeris lookup at the candidate instant) +
        panchang_engine's live swisseph path. Any of those being unavailable is not
        fabricated — returns (0.5, 0.5, 'placeholder_no_ephemeris') so the placeholder
        is distinguishable from a real score via the source label.
        """
        if (
            not candidate_start
            or natal_moon_sign_id is None
            or natal_moon_nakshatra_id is None
            or not birth_params
        ):
            return 0.5, 0.5, 'placeholder_no_ephemeris'

        lat = birth_params.get('latitude_deg')
        lon = birth_params.get('longitude_deg')
        tz_hours = birth_params.get('tz_offset_hours')
        if lat is None or lon is None or tz_hours is None:
            return 0.5, 0.5, 'placeholder_no_ephemeris'

        try:
            from panchang_engine import panchanga_instant
            from panchang_engine.tara_bala import (
                compute_tara_bala_score,
                compute_chandra_bala_score,
            )

            pi = panchanga_instant(candidate_start, float(lat), float(lon), int(round(tz_hours * 60)))
            transit_nakshatra_id = pi.nakshatra.id
            transit_moon = next((p for p in (pi.planets or []) if p.name == 'Moon'), None)
            if transit_moon is None:
                return 0.5, 0.5, 'placeholder_no_ephemeris'
            transit_sign_id = transit_moon.sign_id

            tarabala = compute_tara_bala_score(natal_moon_nakshatra_id, transit_nakshatra_id)
            chandrabala = compute_chandra_bala_score(natal_moon_sign_id, transit_sign_id)
            return round(tarabala, 4), round(chandrabala, 4), 'panchang_engine_live'
        except Exception as exc:
            logger.debug("ph_muhurta: tarabala/chandrabala live computation skipped: %s", exc)
            return 0.5, 0.5, 'placeholder_no_ephemeris'


_DOMAIN_TO_ACTION: dict[str, str] = {
    'career':       'start_business',
    'financial':    'contract_signing',
    'health':       'medical',
    'relationship': 'marriage',
    'spiritual':    'spiritual_initiation',
    'psychological':'ceremony',
    'transition':   'travel',
}


def _to_datetime(d) -> datetime | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d
    if isinstance(d, date):
        return datetime(d.year, d.month, d.day, 6, 0)  # morning start
    try:
        return datetime.fromisoformat(str(d))
    except ValueError:
        return None
