"""
ka_sangam — Convergence engine (L3 K4-a).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
Orchestrator owns the transaction — writer must NOT commit or rollback
NEVER writes to any bodha_* table.

Reads kala_activation_predicates (written by ka_yojaka), runs Mode A + Mode B
convergence search, inserts ranked windows into kala_convergence.
"""
import json
import logging
from datetime import date

import psycopg

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register
from services.ka_sangam.engine import (
    mode_a_search,
    mode_b_sweep,
    mode_c_subsystem_period,
    mode_d_av_bindhu,
    convergence_score,
    confidence_label,
    independent_current_count,
    _date_to_jd,
    EnrichmentContext,
)
from services.ka_dasha_kala.service import KaDashaKalaService
from services.ka_gochara.service import KaGocharaService
from services.ka_muhurta_seva.service import KaMuhurtaSevaService

# Native birth location (Bhubaneswar, Odisha) — required by muhurta/panchanga service.
# lat/lon from FORENSIC data; tz_offset_minutes = 330 (IST = UTC+5:30).
_NATIVE_LOCATION: dict = {
    'lat': 20.2961,
    'lon': 85.8245,
    'tz_offset_minutes': 330,
}

logger = logging.getLogger(__name__)

# Classical sign-lord table (1=Aries … 12=Pisces) for DISPOSITOR_RELATIONAL house-lord resolution.
_SIGN_LORDS: dict[int, str] = {
    1: 'Mars', 2: 'Venus', 3: 'Mercury', 4: 'Moon',
    5: 'Sun',  6: 'Mercury', 7: 'Venus', 8: 'Mars',
    9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Jupiter',
}
_LAGNA_SIGN_NUM: dict[str, int] = {
    'Aries': 1, 'Taurus': 2, 'Gemini': 3, 'Cancer': 4,
    'Leo': 5, 'Virgo': 6, 'Libra': 7, 'Scorpio': 8,
    'Sagittarius': 9, 'Capricorn': 10, 'Aquarius': 11, 'Pisces': 12,
}

# Horizon: 7-year forward window (near tier).
# Raised from 5y → 7y: provides ~40% more actionable near-term windows while
# remaining within the 15-min orphan watchdog budget.
_HORIZON_YEARS = 7
_MAX_PREDICATES = 200  # raised from 60: covers ~0.3% of 66,738 signals at full breadth

# U2 lifetime tier: dāśā-boundary-anchored convergence over the native's full life.
_LIFETIME_HORIZON_YEARS = 100   # birth_date → birth_date + 100y
_LIFETIME_MAX_PREDICATES = 60   # raised from 24: broader lifetime evidence
_LIFETIME_MAX_ROWS = 40_000     # raised from 13k to match expanded predicate budget


@register('ka_sangam')
class KaSangamWriter(WriterBase):
    """
    Convergence engine: Mode A (daśā-prior funnel) + Mode B (off-daśā sweep).
    Inserts into kala_convergence with full rigor-stratum columns.

    HEAVY writer: one 'near' substep + one 'lifetime:N' substep per lifetime predicate.
    Each substep heartbeats independently so the 15-min orphan watchdog is never hit.
    """
    asset_id = 'ka_sangam'
    has_substeps = True

    # ── plan ─────────────────────────────────────────────────────────────────

    def plan_substeps(self, ctx) -> list[SubStep]:
        """Load predicates + services once; store on self for run_substep."""
        conn      = ctx.db_conn
        chart_id  = ctx.config['chart_id']
        self._chart_id = chart_id

        # Load top predicates
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            # NOTE: dasha_eligibility_rule_jsonb->>'eligibility_score' is never
            # populated by ka_yojaka/binder.py — the original ORDER BY on it was
            # a no-op (all NULL, NULLS LAST → arbitrary DB order). Rank by
            # bodha_msr_signals.dignity_score instead, which IS populated and is
            # already used downstream (pd['dignity_score']) as the real per-signal
            # strength signal — so the "top predicates" LIMIT is meaningful again.
            cur.execute(
                """
                SELECT p.id, p.chart_id, p.ayanamsha_id, p.signal_id, p.signature_class,
                       p.dasha_eligibility_rule_jsonb, p.transit_trigger_jsonb,
                       p.strength_affliction_hook_jsonb, p.derivation_ledger_jsonb
                FROM kala_activation_predicates p
                LEFT JOIN bodha_msr_signals s ON s.signal_id = p.signal_id
                WHERE p.chart_id = %s
                ORDER BY s.dignity_score DESC NULLS LAST
                LIMIT %s
                """,
                (chart_id, _MAX_PREDICATES),
            )
            predicates = cur.fetchall()

        logger.info("ka_sangam: loaded %d predicates for chart %s", len(predicates), chart_id)

        # Services
        self._dks = KaDashaKalaService(conn)
        try:
            import swisseph as swe
            self._gs = KaGocharaService(swe)
        except Exception as exc:
            logger.warning("ka_sangam: KaGocharaService unavailable: %s", exc)
            self._gs = None
        try:
            self._muhurta = KaMuhurtaSevaService()
        except Exception as exc:
            logger.warning("ka_sangam: KaMuhurtaSevaService unavailable: %s", exc)
            self._muhurta = None

        # Signal enrichment maps
        signal_ids = list({str(p['signal_id']) for p in predicates if p['signal_id']})
        dignity_map:    dict[str, float]    = {}
        graha_name_map: dict[str, str|None] = {}
        house_num_map:  dict[str, int|None] = {}
        # B4-src: domain map — primary domain from domains_affected_array[0]
        domain_map:     dict[str, str|None] = {}
        if signal_ids:
            with conn.cursor() as cur:
                placeholders = ','.join(['%s'] * len(signal_ids))
                cur.execute(
                    f"SELECT signal_id, dignity_score, "
                    f"configuration_jsonb->>'fact_value_text' AS graha_name, "
                    f"(configuration_jsonb->>'fact_value_num')::numeric::int AS house_num, "
                    f"domains_affected_array "
                    f"FROM bodha_msr_signals WHERE signal_id IN ({placeholders})",
                    signal_ids,
                )
                for row in cur.fetchall():
                    sid = str(row['signal_id'])
                    dignity_map[sid]    = float(row['dignity_score']) if row['dignity_score'] is not None else 0.5
                    graha_name_map[sid] = row['graha_name']
                    house_num_map[sid]  = row['house_num']
                    # B4-src: extract first domain from array; None when absent
                    da = row['domains_affected_array']
                    domain_map[sid] = da[0] if da else None

        # Build normalised pred_dicts
        pred_dicts: list[dict] = []
        for pred in predicates:
            pd = dict(pred)
            sig_id = pd.get('signal_id')
            pd['dignity_score'] = dignity_map.get(str(sig_id), 0.5) if sig_id else 0.5
            # B4-src: carry primary domain through to convergence row
            pd['primary_domain'] = domain_map.get(str(sig_id)) if sig_id else None
            for jf in ('dasha_eligibility_rule_jsonb', 'transit_trigger_jsonb',
                       'strength_affliction_hook_jsonb', 'derivation_ledger_jsonb'):
                if isinstance(pd.get(jf), str):
                    pd[jf] = json.loads(pd[jf])
                elif pd.get(jf) is None:
                    pd[jf] = {}
            pred_dicts.append(pd)

        house_lord_map = self._build_house_lord_map(conn, chart_id)
        for pd in pred_dicts:
            sid = str(pd.get('signal_id') or '')
            sc  = (pd.get('signature_class') or '').upper()
            if 'DIGNITY' in sc:
                pd['graha_name'] = graha_name_map.get(sid)
            if 'DISPOSITOR_RELATIONAL' in sc:
                hn = house_num_map.get(sid)
                pd['dispositor_lord'] = house_lord_map.get(hn) if hn else None

        self._pred_dicts = pred_dicts
        self._lt_preds   = pred_dicts[:_LIFETIME_MAX_PREDICATES]

        # Build U3 enrichment context (C7/C11/C12/C13 currents)
        self._enrichment_ctx = self._build_enrichment_context(conn, chart_id)

        # Birth year for lifetime horizon
        self._birth_year = self._derive_birth_year(conn, chart_id)

        # Substep list: one near + one per lifetime predicate
        steps = [SubStep(key='near', label='Near tier (5yr)')]
        for i, p in enumerate(self._lt_preds):
            sc = p.get('signature_class', '')
            steps.append(SubStep(key=f'lifetime:{i}', label=f'Lifetime pred {i} ({sc})'))
        return steps

    # ── dispatch ─────────────────────────────────────────────────────────────

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        conn     = ctx.db_conn
        chart_id = self._chart_id
        dry_run  = getattr(ctx, 'dry_run', False)

        if step.key == 'near':
            return self._substep_near(conn, chart_id, dry_run)

        idx = int(step.key.split(':', 1)[1])
        return self._substep_lifetime(conn, chart_id, idx, dry_run)

    # ── substep implementations ───────────────────────────────────────────────

    def _substep_near(self, conn, chart_id: str, dry_run: bool) -> WriterResult:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_convergence WHERE chart_id = %s AND horizon_tier = 'near'",
                        (chart_id,))
            # Clear lifetime rows here so stale rows are removed even when
            # _lt_preds is empty and _substep_lifetime is never called.
            cur.execute(
                "DELETE FROM kala_convergence WHERE chart_id = %s AND horizon_tier = 'lifetime'",
                (chart_id,),
            )

        today        = date.today()
        horizon_end  = date(today.year + _HORIZON_YEARS, today.month, today.day)
        def _keepalive():
            with conn.cursor() as _cur:
                _cur.execute("SELECT 1")

        near_windows = self._generate_windows(
            pred_dicts        = self._pred_dicts,
            horizon_start     = today,
            horizon_end       = horizon_end,
            dasha_kala_service= self._dks,
            gochara_service   = self._gs,
            chart_id          = chart_id,
            keepalive         = _keepalive,
            enrichment_context= self._enrichment_ctx,
            muhurta_service   = self._muhurta,
        )
        near_deduped = self._dedup(near_windows)
        logger.info("ka_sangam: NEAR tier — %d windows for chart %s", len(near_deduped), chart_id)

        rows = 0
        if not dry_run:
            with conn.cursor() as cur:
                rows = self._insert_windows(cur, chart_id, near_deduped, 'near')
        return WriterResult(asset_id='ka_sangam', rows_inserted=rows)

    def _substep_lifetime(self, conn, chart_id: str, idx: int, dry_run: bool) -> WriterResult:
        pred      = self._lt_preds[idx]
        signal_id = pred.get('signal_id')

        # Idempotency: lifetime rows were bulk-cleared in _substep_near before any
        # lifetime substep runs; no additional full-table delete needed here.
        with conn.cursor() as cur:
            if signal_id:
                cur.execute(
                    "DELETE FROM kala_convergence WHERE chart_id = %s AND signal_id = %s::uuid AND horizon_tier = 'lifetime'",
                    (chart_id, str(signal_id)),
                )

        if self._birth_year is None:
            return WriterResult(asset_id='ka_sangam', rows_inserted=0,
                                notes='skipped lifetime substep: _birth_year is None (chart_dashas has no level_n=1 rows)')
        horizon_start = date(self._birth_year, 1, 1)
        horizon_end   = date(self._birth_year + _LIFETIME_HORIZON_YEARS, 12, 31)
        def _keepalive():
            with conn.cursor() as _cur:
                _cur.execute("SELECT 1")

        windows       = self._generate_windows(
            pred_dicts        = [pred],
            horizon_start     = horizon_start,
            horizon_end       = horizon_end,
            dasha_kala_service= self._dks,
            gochara_service   = self._gs,
            chart_id          = chart_id,
            keepalive         = _keepalive,
            enrichment_context= self._enrichment_ctx,
            muhurta_service   = self._muhurta,
        )
        deduped = self._dedup(windows)
        logger.info("ka_sangam: LIFETIME pred %d/%d — %d windows for chart %s",
                    idx, len(self._lt_preds) - 1, len(deduped), chart_id)

        rows = 0
        if not dry_run:
            with conn.cursor() as cur:
                rows = self._insert_windows(cur, chart_id, deduped, 'lifetime')
        return WriterResult(asset_id='ka_sangam', rows_inserted=rows)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _generate_windows(self, pred_dicts, horizon_start, horizon_end,
                          dasha_kala_service, gochara_service, chart_id,
                          keepalive=None, enrichment_context=None,
                          muhurta_service=None) -> list[dict]:
        """Run Mode A + Mode B (or Mode C for SUBSYSTEM) for every predicate.

        SUBSYSTEM predicates are routed to mode_c_subsystem_period (sign-ingress
        trigger) instead of the aspect-based Mode A/B engine.
        keepalive: optional callable to prevent idle-in-transaction timeout.
        enrichment_context: EnrichmentContext for U3 current scoring.
        muhurta_service: KaMuhurtaSevaService for panchanga_quality + tara_bala.
        B4-src: stamps primary_domain onto every window dict produced.
        """
        horizon_start_jd = _date_to_jd(horizon_start)
        horizon_end_jd   = _date_to_jd(horizon_end)
        all_windows: list[dict] = []
        for pred_dict in pred_dicts:
            sig_id    = pred_dict.get('signal_id')
            sig_class = (pred_dict.get('signature_class') or '').upper()
            # B4-src: primary domain from MSR signal (carried through plan_substeps)
            primary_domain = pred_dict.get('primary_domain')

            # Route SUBSYSTEM predicates to Mode C (period-based ingress trigger)
            if 'SUBSYSTEM' in sig_class:
                try:
                    new_windows = mode_c_subsystem_period(
                        predicate=pred_dict,
                        horizon_start_jd=horizon_start_jd,
                        horizon_end_jd=horizon_end_jd,
                        gochara_service=gochara_service,
                        enrichment_context=enrichment_context,
                    )
                    for w in new_windows:
                        w['primary_domain'] = primary_domain
                    all_windows.extend(new_windows)
                except Exception as exc:
                    logger.warning("ka_sangam: Mode C failed for signal %s: %s", sig_id, exc)
                if keepalive:
                    keepalive()
                continue

            try:
                new_windows_a = mode_a_search(
                    predicate=pred_dict,
                    horizon_start_jd=horizon_start_jd,
                    horizon_end_jd=horizon_end_jd,
                    dasha_kala_service=dasha_kala_service,
                    gochara_service=gochara_service,
                    muhurta_service=muhurta_service,
                    chart_id=chart_id,
                    enrichment_context=enrichment_context,
                    native_location=_NATIVE_LOCATION,
                )
                for w in new_windows_a:
                    w['primary_domain'] = primary_domain
                all_windows.extend(new_windows_a)
            except Exception as exc:
                logger.warning("ka_sangam: Mode A failed for signal %s: %s", sig_id, exc)
            if keepalive:
                keepalive()
            try:
                new_windows_b = mode_b_sweep(
                    signal_id=sig_id,
                    predicate=pred_dict,
                    horizon_start_jd=horizon_start_jd,
                    horizon_end_jd=horizon_end_jd,
                    gochara_service=gochara_service,
                    magnitude_threshold=0.3,
                    enrichment_context=enrichment_context,
                    muhurta_service=muhurta_service,
                    native_location=_NATIVE_LOCATION,
                )
                for w in new_windows_b:
                    w['primary_domain'] = primary_domain
                all_windows.extend(new_windows_b)
            except Exception as exc:
                logger.warning("ka_sangam: Mode B failed for signal %s: %s", sig_id, exc)
            if keepalive:
                keepalive()

            # O7: Mode D — SAV-bindhu activation windows for strong signs
            # Only run for the first predicate per horizon call to avoid duplicate windows.
            # Mode D is sign-level and predicate-agnostic; running it for every predicate
            # produces N×K duplicate windows with different signal_ids that bypass the dedup
            # key check (which includes signal_id).
            if pred_dicts and pred_dict is pred_dicts[0]:
                try:
                    new_windows_d = mode_d_av_bindhu(
                        predicate=pred_dict,
                        horizon_start_jd=horizon_start_jd,
                        horizon_end_jd=horizon_end_jd,
                        gochara_service=gochara_service,
                        enrichment_context=enrichment_context,
                    )
                    for w in new_windows_d:
                        w['primary_domain'] = primary_domain
                    all_windows.extend(new_windows_d)
                except Exception as exc:
                    logger.warning("ka_sangam: Mode D failed for signal %s: %s", sig_id, exc)
                if keepalive:
                    keepalive()
        return all_windows

    def _derive_birth_year(self, conn, chart_id: str) -> int | None:
        """Derive birth year from the earliest MD start in chart_dashas. Returns None if unavailable."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT MIN(start_date) AS birth_date FROM chart_dashas WHERE chart_id = %s AND level_n = 1",
                (chart_id,),
            )
            row = cur.fetchone()
            if row and row['birth_date']:
                return row['birth_date'].year
        return None

    @staticmethod
    def _dedup(all_windows: list[dict]) -> list[dict]:
        """Deduplicate by (mode, peak_date, signal_id) — keep highest score."""
        seen: dict[tuple, dict] = {}
        for w in all_windows:
            key = (w.get('mode'), w.get('peak_date'), str(w.get('signal_id', '')))
            if key not in seen or w['convergence_score'] > seen[key]['convergence_score']:
                seen[key] = w
        return sorted(seen.values(), key=lambda w: w['convergence_score'], reverse=True)

    def _insert_windows(self, cur, chart_id, deduped: list[dict], horizon_tier: str) -> int:
        """Insert a tier's deduped windows into kala_convergence; return count."""
        rows_inserted = 0
        for w in deduped:
                cs = w.get('convergence_score', 0.0)
                orb_s = w.get('orb_strength')
                c_label = confidence_label(cs)

                # Compute independent_current_count from constituent_factors
                cf   = w.get('constituent_factors', {})
                mode = w.get('mode', 'A')
                currents = {
                    'dasha': bool(cf.get('dasha_score', 0) > 0.3),
                    'nakshatra_overlay': 'nakshatra' in cf,
                    # Mode C (SUBSYSTEM) and Mode D (AV-bindhu) have no point transit;
                    # Mode A/B always do
                    'transit': mode in ('A', 'B'),
                    # Newly wired currents
                    'panchanga': bool(cf.get('c_panchanga_quality', 0) > 0.0),
                    'benefic_dristi': bool(cf.get('c_benefic_dristi', 0) > 0.0),
                    'cross_dasha_agreement': bool(cf.get('c_cross_dasha_agreement', 0) > 0.0),
                    'nakshatra_subsystem': bool(cf.get('c_nakshatra_subsystem', 0) > 0.0),
                    # U3 C7-C12 currents (Mode D: ashtakavarga_transit_potency from sav_bindhu)
                    'ashtakavarga_transit_potency': (
                        bool(cf.get('c7_ashtakavarga_potency', 0) > 0.0)
                        or (mode == 'D' and bool(cf.get('sav_bindhu', 0) >= 28))
                    ),
                    'eclipse_proximity': bool(cf.get('c8_eclipse_proximity', 0) > 0.0),
                    'transit_to_transit': bool(cf.get('c9_transit_to_transit', 0) > 0.0),
                    'station_retrograde': bool(cf.get('c10_station_retrograde', 0) > 0.0),
                    'tajika_annual_reinforcement': bool(cf.get('c12_tajika_reinforcement', 0) > 0.0),
                    'school_consensus': bool(cf.get('c13_school_consensus', 0) > 0.0),
                }
                icc = independent_current_count(currents)

                cur.execute(
                    """
                    INSERT INTO kala_convergence (
                        chart_id, window_start, window_end, convergence_score,
                        constituent_factors, source_citation, computed_at,
                        signal_id, mode, peak_date, orb_strength, rarity_years,
                        confidence_score, confidence_label,
                        independent_current_count, is_off_dasha_discovery,
                        horizon_tier, domain
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s::jsonb, %s, NOW(),
                        %s, %s, %s, %s, %s,
                        %s, %s,
                        %s, %s,
                        %s, %s
                    )
                    """,
                    (
                        chart_id,
                        w.get('window_start'),
                        w.get('window_end'),
                        cs,
                        json.dumps(w.get('constituent_factors', {})),
                        w.get('source_citation', ''),
                        str(w.get('signal_id')) if w.get('signal_id') else None,
                        w.get('mode'),
                        w.get('peak_date'),
                        orb_s,
                        w.get('rarity_years'),  # CF.L3.4: real planet-period rarity
                        round(min(1.0, icc / 13.0), 4),  # confidence_score = ICC/13 currents (C10 fix: distinct from convergence_score)
                        c_label,
                        icc,
                        w.get('is_off_dasha_discovery', False),
                        horizon_tier,
                        # B4-src: domain from originating MSR signal's domains_affected_array[0]
                        w.get('primary_domain'),
                    ),
                )
                rows_inserted += 1
        return rows_inserted

    def _build_enrichment_context(self, conn, chart_id: str) -> 'EnrichmentContext':
        """Pre-fetch U3 enrichment data from DB for C7/C11/C12/C13 currents.

        All fetches are SAVEPOINT-guarded soft dependencies — partial context
        is better than empty. Returns EnrichmentContext.empty() if all fail.
        """
        ashtakavarga_bindu: dict[str, dict[int, int]] = {}
        vedha_rules: list[dict] = []
        tajika_year_lords: list[dict] = []
        # school_consensus_by_domain: pre-U4 default — not yet built; stays empty

        # C7: ashtakavarga bindus from chart_facts
        # Schema: fact_category='ashtakavarga_bindu', fact_subject='<Planet>-HOUSE_<N>',
        # fact_key='bindus', fact_value_num=bindu_count, ayanamsha_id='lahiri_chitrapaksha'
        # B6 fix: stored value is 'lahiri_chitrapaksha', not bare 'lahiri'.
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_enrichment_ashtak")
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_subject, fact_value_num
                    FROM chart_facts
                    WHERE chart_id = %s
                      AND fact_category = 'ashtakavarga_bindu'
                      AND ayanamsha_id = 'lahiri_chitrapaksha'
                      AND fact_key = 'bindus'
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    # fact_subject like 'Sun-HOUSE_3' or 'SARVA-HOUSE_3'
                    subj = row['fact_subject'] or ''
                    if '-HOUSE_' not in subj:
                        continue
                    parts = subj.rsplit('-HOUSE_', 1)
                    if len(parts) != 2:
                        continue
                    planet, house_str = parts
                    try:
                        house_num = int(house_str)
                        bindus = int(row['fact_value_num']) if row['fact_value_num'] is not None else 0
                        if planet not in ashtakavarga_bindu:
                            ashtakavarga_bindu[planet] = {}
                        ashtakavarga_bindu[planet][house_num] = bindus
                    except (ValueError, TypeError):
                        continue
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_enrichment_ashtak")
        except Exception as exc:
            logger.debug("ka_sangam: ashtakavarga fetch skipped: %s", exc)
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_enrichment_ashtak")
            except Exception:
                pass

        # C11: vedha rules from bg_transit_rules
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_enrichment_vedha")
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT graha, primary_house, vedha_house
                    FROM bg_transit_rules
                    WHERE rule_type = 'vedha'
                    """
                )
                for row in cur.fetchall():
                    vedha_rules.append({
                        'graha': row['graha'],
                        'transit_to_house': row['primary_house'],
                        'vedha_house': row['vedha_house'],
                    })
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_enrichment_vedha")
        except Exception as exc:
            logger.debug("ka_sangam: vedha_rules fetch skipped: %s", exc)
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_enrichment_vedha")
            except Exception:
                pass

        # C12: tajika year lords (may not exist yet — pre-L3 builds)
        try:
            with conn.cursor() as sp:
                sp.execute("SAVEPOINT sp_enrichment_tajika")
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT varsha_year, varshesha, muntha
                    FROM l1_tajik_varsha_year_lords
                    WHERE chart_id = %s
                    ORDER BY varsha_year
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    tajika_year_lords.append({
                        'varsha_year': row['varsha_year'],
                        'varshesha': row['varshesha'],
                        'muntha': row['muntha'],
                    })
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_enrichment_tajika")
        except Exception as exc:
            logger.debug("ka_sangam: tajika_year_lords fetch skipped: %s", exc)
            try:
                with conn.cursor() as sp:
                    sp.execute("ROLLBACK TO SAVEPOINT sp_enrichment_tajika")
            except Exception:
                pass

        if ashtakavarga_bindu or vedha_rules or tajika_year_lords:
            logger.info(
                "ka_sangam: EnrichmentContext built — ashtak_planets=%d, vedha_rules=%d, tajika_years=%d",
                len(ashtakavarga_bindu), len(vedha_rules), len(tajika_year_lords),
            )
        else:
            logger.warning("ka_sangam: EnrichmentContext is empty — C7/C11/C12 will score 0.0")

        return EnrichmentContext(
            ashtakavarga_bindu=ashtakavarga_bindu if ashtakavarga_bindu else None,
            vedha_rules=vedha_rules if vedha_rules else None,
            tajika_year_lords=tajika_year_lords if tajika_year_lords else None,
        )

    def _build_house_lord_map(self, conn, chart_id: str) -> dict[int, str]:
        """
        Build {house_num: lord_name} for DISPOSITOR_RELATIONAL predicate enrichment.
        Derives lords from lagna sign via classical whole-sign house assignment.
        Falls back to Aries (this native's lagna) on any query failure.
        """
        lagna_sign = 'Aries'
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT fact_value_text FROM chart_facts "
                    "WHERE chart_id = %s AND fact_subject = 'LAGNA' AND fact_key = 'sign' LIMIT 1",
                    (chart_id,),
                )
                row = cur.fetchone()
                if row and row['fact_value_text']:
                    lagna_sign = row['fact_value_text']
        except Exception as exc:
            logger.warning("ka_sangam: could not fetch lagna sign for %s: %s", chart_id, exc)
        lagna_num = _LAGNA_SIGN_NUM.get(lagna_sign, 1)
        return {
            house: _SIGN_LORDS[(lagna_num + house - 2) % 12 + 1]
            for house in range(1, 13)
        }
