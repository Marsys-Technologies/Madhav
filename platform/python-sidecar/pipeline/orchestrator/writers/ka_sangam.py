"""
ka_sangam — Convergence engine (L3 K4-a).
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
Orchestrator owns the transaction — writer must NOT commit or rollback
NEVER writes to any bodha_* table.

Reads kala_activation_predicates (written by ka_yojaka), runs Mode A + Mode B
convergence search, inserts ranked windows into kala_convergence.
"""
import hashlib
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
    relative_confidence_labels,
    independent_current_count,
    _date_to_jd,
    _NAK_NAME_TO_IDX,
    _SIGN_NAME_TO_IDX,
    EnrichmentContext,
    NativeChartContext,
    derive_sade_sati_signs,
    derive_sade_sati_severity,
)
from services.ka_dasha_kala.service import KaDashaKalaService
from services.ka_gochara.service import KaGocharaService
from services.ka_muhurta_seva.service import KaMuhurtaSevaService
from services.kala_trigger.trigger import compute_trigger_currents, compose_with_ka_sangam

# ── D-3 T-6: TRIGGER wiring at the ADMITTED weights ───────────────────────────
# wave/D-3/ADMIT (receipted ACCEPT) found additive=0.2/suppressive=0.2 for
# BOTH weight keys on each side scores best on the train split -- NOT
# services.kala_trigger.trigger's own unratified 0.5/0.6 defaults. T-4
# PERMISSION was admission-REJECTED (degrades train score) and is
# deliberately NOT wired into this score anywhere in this file.
TRIGGER_ADMITTED_ADDITIVE_WEIGHTS = {'guru_shani_double_transit': 0.2, 'saham_activation': 0.2}
TRIGGER_ADMITTED_SUPPRESSIVE_WEIGHTS = {'malefic_transit_over_mechanism': 0.2, 'papa_kartari_sandwich': 0.2}


def apply_trigger_suppression(windows: list[dict], *, chart_id: str, target_lon,
                               gochara_service, vedha_rules, moon_sign_idx) -> list[dict]:
    """
    D-3 T-6: compose each window's convergence_score with T-5's TRIGGER
    suppressive term (malefic-transit-over-mechanism + papa-kartari-sandwich)
    via compose_with_ka_sangam, at the ADMITTED 0.2/0.2 weights above. This is
    the headline TRIGGER deliverable per services/kala_trigger/trigger.py's
    own module docstring: "the first place ... a current can push a score
    DOWN below what the additive terms alone would produce" (CR-89).

    Deliberately NOT applied in this pass (named follow-ups, T-6 claim):
    guru_shani_double_transit / saham_activation additive currents (need
    dasha_lord + saham_lord resolution — the day/night-birth Dhana Saham
    formula lord lookup — out of this pass's scope) and the school_consensus
    informational current (needs EnrichmentContext.school_consensus_by_domain,
    a separate documented gap). PERMISSION (T-4) is never applied anywhere —
    admission-REJECTED.

    Safe no-op when gochara_service is None (mirrors every other U3 current's
    None-guard in services.ka_sangam.engine) — a build without a live
    gochara_service serves the pre-TRIGGER convergence_score unchanged, never
    raises.
    """
    if gochara_service is None:
        return windows
    for w in windows:
        try:
            cf = w.get('constituent_factors') or {}
            ws, we = w.get('window_start'), w.get('window_end')
            if ws is None or we is None:
                continue
            w_jd_start = _date_to_jd(ws)
            w_jd_end = _date_to_jd(we)
            sign_name = cf.get('sign')
            transit_sign = (_SIGN_NAME_TO_IDX[sign_name] + 1) if sign_name in _SIGN_NAME_TO_IDX else None
            trig = compute_trigger_currents(
                chart_id=chart_id,
                mechanism_lon=target_lon,
                target_lon=target_lon,
                transit_sign_idx_1based=transit_sign,
                moon_sign_idx_0based=moon_sign_idx,
                w_jd_start=w_jd_start,
                w_jd_end=w_jd_end,
                gochara_service=gochara_service,
                vedha_rules=vedha_rules,
                vedha_planet=cf.get('planet'),
                signature_class=cf.get('signature_class', 'UNKNOWN'),
                additive_weights=TRIGGER_ADMITTED_ADDITIVE_WEIGHTS,
                suppressive_weights=TRIGGER_ADMITTED_SUPPRESSIVE_WEIGHTS,
            )
            pre_score = float(w.get('convergence_score', 0.0) or 0.0)
            new_score = compose_with_ka_sangam(pre_score, trig)
            w['convergence_score'] = round(new_score, 4)
            cf['convergence_score_pre_trigger'] = pre_score
            cf['trigger_suppressive_applied'] = trig['suppressive']
            cf['trigger_weights_used'] = trig['weights_used']
            w['constituent_factors'] = cf
        except Exception as exc:
            logger.debug("ka_sangam: TRIGGER suppression skipped for a window: %s", exc)
    return windows

# CR-87 fix: the module-level _NATIVE_LOCATION constant (hardcoded to
# Bhubaneswar, lat/lon of chart 482012f1) has been DELETED — not defaulted.
# Every chart's location, janma nakshatra, and Moon sign are now resolved
# per-chart in plan_substeps() via _resolve_native_chart_context() and carried
# on self._native_ctx (a NativeChartContext). No fallback to Bhubaneswar
# anywhere in this writer's production path.

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

# Bump when substep SEMANTICS change (what a given substep_key computes/writes),
# so any in-flight resume ledger from an older writer is treated as a different
# build and replanned-all rather than resumed against stale semantics.
_KA_SANGAM_RESUME_VERSION = 1
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
                -- p.id is a STABLE tiebreaker: without it, ties in dignity_score
                -- give arbitrary DB order, so 'lifetime:i' could refer to a
                -- different predicate across resume attempts (silent skip/orphan).
                -- With it, the substep→predicate mapping is deterministic for a
                -- fixed predicate set — a hard prerequisite for correct resumption.
                ORDER BY s.dignity_score DESC NULLS LAST, p.id ASC
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

        # CR-87: resolve THIS chart's janma nakshatra, Moon sign, and birth
        # location — never another chart's hardcoded values.
        self._native_ctx = self._resolve_native_chart_context(
            conn, chart_id, ctx.config.get('birth_params'),
        )

        # Birth year for lifetime horizon
        self._birth_year = self._derive_birth_year(conn, chart_id)

        # Substep list: one near + one per lifetime predicate
        steps = [SubStep(key='near', label='Near tier (5yr)')]
        for i, p in enumerate(self._lt_preds):
            sc = p.get('signature_class', '')
            steps.append(SubStep(key=f'lifetime:{i}', label=f'Lifetime pred {i} ({sc})'))

        # ── Cross-attempt substep resumption (migration 436 build_substep_progress) ──
        # This writer's ~61 substeps (each lifetime substep is a 100-year convergence
        # scan) can outlast a single DB connection through the Cloud SQL Auth Proxy.
        # Without resumption, every retry re-ran ALL substeps from scratch and could
        # never finish. Here plan_substeps() decides — per §N.3 (delete-then-insert
        # REPLACES, never accretes) — whether to RESUME (skip already-committed
        # substeps of the SAME build) or REPLAN-ALL (a changed/first build). All of
        # this lives in the writer; the FROZEN orchestrator/WriterBase contract is
        # untouched (the orchestrator still owns the per-substep transaction/savepoint;
        # this method only returns a (possibly shorter) substep list).
        self._resume_fingerprint = self._compute_build_fingerprint(chart_id)
        self._resume_skipped = 0
        if getattr(ctx, 'dry_run', False):
            return steps  # dry runs never delete data or touch the ledger

        completed = self._load_completed_substeps(conn, chart_id, self._resume_fingerprint)
        if completed is None:
            # First run, or a prior/changed build (fingerprint mismatch). Delete-and-
            # replan-all: clear EVERY kala_convergence row for this chart + the stale
            # ledger, then run all substeps fresh — no stale accretion possible. (These
            # deletes ride the orchestrator's ambient transaction and commit atomically
            # with the first substep; if the connection dies before that commit they
            # roll back, leaving the prior data intact for the next attempt.)
            with conn.cursor() as cur:
                cur.execute("DELETE FROM kala_convergence WHERE chart_id = %s", (chart_id,))
                cur.execute(
                    "DELETE FROM build_substep_progress WHERE chart_id = %s AND asset_id = 'ka_sangam'",
                    (chart_id,),
                )
            logger.info("ka_sangam: fresh/replan build for chart %s — %d substeps", chart_id, len(steps))
            return steps

        remaining = [s for s in steps if s.key not in completed]
        self._resume_skipped = len(steps) - len(remaining)
        logger.info(
            "ka_sangam: RESUMING build for chart %s — %d/%d substeps already committed, %d remaining",
            chart_id, self._resume_skipped, len(steps), len(remaining),
        )
        return remaining

    # ── dispatch ─────────────────────────────────────────────────────────────

    def run_substep(self, ctx, step: SubStep) -> WriterResult:
        conn     = ctx.db_conn
        chart_id = self._chart_id
        dry_run  = getattr(ctx, 'dry_run', False)

        if step.key == 'near':
            return self._substep_near(conn, chart_id, dry_run)

        idx = int(step.key.split(':', 1)[1])
        return self._substep_lifetime(conn, chart_id, idx, dry_run)

    # ── resumption helpers (migration 436) ────────────────────────────────────

    def _compute_build_fingerprint(self, chart_id: str) -> str:
        """Stable identity of THIS build's inputs — deliberately NOT the per-attempt
        run_id/build_id (which changes on every retry, so keying resume on it would
        treat each retry as a new build and never actually resume). Two attempts
        with the same upstream predicate set, writer version, birth year, and
        near-tier reference date belong to the SAME build and may resume across a
        dropped connection; any change to those inputs replans-all (§N.3). `today`
        is included because the near tier is date-relative — a build that legitimately
        crosses midnight should replan its near tier rather than resume it stale."""
        sig_ids = sorted(str(p.get('signal_id')) for p in self._pred_dicts if p.get('signal_id'))
        parts = [
            f"v={_KA_SANGAM_RESUME_VERSION}",
            f"chart={chart_id}",
            f"birth_year={self._birth_year}",
            f"today={date.today().isoformat()}",
            f"npreds={len(sig_ids)}",
            "sigs=" + ",".join(sig_ids),
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()

    def _load_completed_substeps(self, conn, chart_id: str, fingerprint: str) -> "set[str] | None":
        """Substep keys already committed for the CURRENT build (fingerprint match)
        → caller skips them (resume). Returns None when the ledger is empty (first
        run) OR holds any row from a different fingerprint (a prior/changed build)
        → caller deletes-all and replans fresh."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT substep_key, build_fingerprint FROM build_substep_progress "
                "WHERE chart_id = %s AND asset_id = 'ka_sangam'",
                (chart_id,),
            )
            rows = cur.fetchall()
        if not rows:
            return None
        if {r['build_fingerprint'] for r in rows} != {fingerprint}:
            return None
        return {r['substep_key'] for r in rows}

    def _record_substep(self, conn, chart_id: str, substep_key: str, rows: int) -> None:
        """Record this substep's completion in the resumption ledger, INSIDE the
        orchestrator-owned per-substep transaction — so the ledger row commits
        atomically with the substep's data rows (durable iff the data is durable,
        rolled back with it on failure). The writer never commits/rolls back/closes;
        the FROZEN orchestrator contract is untouched."""
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO build_substep_progress
                       (chart_id, asset_id, substep_key, build_fingerprint, rows_written, completed_at)
                   VALUES (%s, 'ka_sangam', %s, %s, %s, now())
                   ON CONFLICT (chart_id, asset_id, substep_key)
                   DO UPDATE SET build_fingerprint = EXCLUDED.build_fingerprint,
                                 rows_written      = EXCLUDED.rows_written,
                                 completed_at      = EXCLUDED.completed_at""",
                (chart_id, substep_key, self._resume_fingerprint, rows),
            )

    # ── substep implementations ───────────────────────────────────────────────

    def _substep_near(self, conn, chart_id: str, dry_run: bool) -> WriterResult:
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_convergence WHERE chart_id = %s AND horizon_tier = 'near'",
                        (chart_id,))
            # Self-scoped delete: only bulk-clear lifetime rows when there are NO
            # lifetime substeps to clear their own (each _substep_lifetime clears
            # its own signal's rows). Making every substep touch only its own rows
            # is what lets a resumed attempt skip already-committed substeps without
            # wiping another substep's committed data — and is what makes a
            # resumed run byte-identical to an uninterrupted one.
            if not self._lt_preds:
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
            native_ctx        = self._native_ctx,
        )
        near_deduped = self._dedup(near_windows)
        logger.info("ka_sangam: NEAR tier — %d windows for chart %s", len(near_deduped), chart_id)

        rows = 0
        if not dry_run:
            with conn.cursor() as cur:
                rows = self._insert_windows(cur, chart_id, near_deduped, 'near')
            self._record_substep(conn, chart_id, 'near', rows)
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
            native_ctx        = self._native_ctx,
        )
        deduped = self._dedup(windows)
        logger.info("ka_sangam: LIFETIME pred %d/%d — %d windows for chart %s",
                    idx, len(self._lt_preds) - 1, len(deduped), chart_id)

        rows = 0
        if not dry_run:
            with conn.cursor() as cur:
                rows = self._insert_windows(cur, chart_id, deduped, 'lifetime')
            self._record_substep(conn, chart_id, f'lifetime:{idx}', rows)
        return WriterResult(asset_id='ka_sangam', rows_inserted=rows)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _generate_windows(self, pred_dicts, horizon_start, horizon_end,
                          dasha_kala_service, gochara_service, chart_id,
                          native_ctx: 'NativeChartContext',
                          keepalive=None, enrichment_context=None,
                          muhurta_service=None) -> list[dict]:
        """Run Mode A + Mode B (or Mode C for SUBSYSTEM) for every predicate.

        SUBSYSTEM predicates are routed to mode_c_subsystem_period (sign-ingress
        trigger) instead of the aspect-based Mode A/B engine.
        keepalive: optional callable to prevent idle-in-transaction timeout.
        enrichment_context: EnrichmentContext for U3 current scoring.
        muhurta_service: KaMuhurtaSevaService for panchanga_quality + tara_bala.
        native_ctx: CR-87 — THIS chart's resolved NativeChartContext (janma
          nakshatra, Moon sign, location). Never another chart's values.
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
                        moon_sign=native_ctx.moon_sign,
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

            # D-3 T-6: target_lon feeds TRIGGER's mechanism_lon/target_lon below —
            # same longitude mode_a_search/mode_b_sweep already scan against.
            target_lon = float((pred_dict.get('transit_trigger_jsonb') or {}).get('target_longitude_deg', 0.0))
            moon_sign_idx = _SIGN_NAME_TO_IDX.get(native_ctx.moon_sign)
            vedha_rules = (enrichment_context.vedha_rules if enrichment_context else None) or None

            try:
                new_windows_a = mode_a_search(
                    predicate=pred_dict,
                    horizon_start_jd=horizon_start_jd,
                    horizon_end_jd=horizon_end_jd,
                    dasha_kala_service=dasha_kala_service,
                    gochara_service=gochara_service,
                    muhurta_service=muhurta_service,
                    chart_id=chart_id,
                    janma_nakshatra_idx=native_ctx.janma_nakshatra_idx,
                    enrichment_context=enrichment_context,
                    native_location=native_ctx.location,
                    moon_sign=native_ctx.moon_sign,  # CR-102 fix (T-6): correct house-from-Moon vedha frame
                )
                # D-3 T-6: TRIGGER suppressive term at the ADMITTED 0.2/0.2 weights
                # (wave/D-3/ADMIT, receipted ACCEPT) — see apply_trigger_suppression docstring.
                new_windows_a = apply_trigger_suppression(
                    new_windows_a, chart_id=chart_id, target_lon=target_lon,
                    gochara_service=gochara_service, vedha_rules=vedha_rules,
                    moon_sign_idx=moon_sign_idx,
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
                    janma_nakshatra_idx=native_ctx.janma_nakshatra_idx,
                    magnitude_threshold=0.3,
                    enrichment_context=enrichment_context,
                    muhurta_service=muhurta_service,
                    native_location=native_ctx.location,
                    moon_sign=native_ctx.moon_sign,  # CR-102 fix (T-6): correct house-from-Moon vedha frame
                )
                new_windows_b = apply_trigger_suppression(
                    new_windows_b, chart_id=chart_id, target_lon=target_lon,
                    gochara_service=gochara_service, vedha_rules=vedha_rules,
                    moon_sign_idx=moon_sign_idx,
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

    def _resolve_native_chart_context(self, conn, chart_id: str, birth_params) -> 'NativeChartContext':
        """CR-87 fix: resolve THIS chart's janma nakshatra, Moon sign, and
        birth location from chart_facts / birth_params — never from another
        chart's hardcoded values.

        Fail-loud by design (LANE0_CR87_HOTFIX.md §2.2 item 4): if any of the
        three required inputs cannot be resolved, raise rather than silently
        falling back to 482012f1's (Abhisek's) values. A loud build failure is
        the correct outcome — proceeding with another chart's constants is
        exactly the CR-87 failure mode.
        """
        moon_nakshatra: str | None = None
        moon_sign: str | None = None
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT fact_key, fact_value_text
                FROM chart_facts
                WHERE chart_id = %s AND fact_subject = 'MOON'
                  AND fact_key IN ('nakshatra', 'sign')
                  AND ayanamsha_id = 'lahiri_chitrapaksha'
                """,
                (chart_id,),
            )
            # BUGFIX (Night-1 guardian rebuild): this connection uses psycopg3's
            # dict_row factory (pipeline/orchestrator/db.py), so each fetched row is
            # a dict, not a tuple. Positional unpacking ("for fact_key, fact_value_text
            # in cur.fetchall()") iterates each dict's KEYS ("fact_key", "fact_value_text"
            # — the literal column-name strings), never the actual values — so
            # moon_nakshatra/moon_sign silently stayed None for every real chart,
            # tripping CR-87's fail-loud guard. Same bug class as the ga_structural_writer
            # dict-row fix (commit 8c96d000) — here in ka_sangam.py's own lookup.
            for row in cur.fetchall():
                fact_key, fact_value_text = row['fact_key'], row['fact_value_text']
                if fact_key == 'nakshatra':
                    moon_nakshatra = fact_value_text
                elif fact_key == 'sign':
                    moon_sign = fact_value_text

        if not moon_nakshatra or moon_nakshatra not in _NAK_NAME_TO_IDX:
            raise RuntimeError(
                f"ka_sangam: could not resolve Moon nakshatra for chart {chart_id} "
                f"from chart_facts (fact_subject='MOON', fact_key='nakshatra', "
                f"ayanamsha_id='lahiri_chitrapaksha') — got {moon_nakshatra!r}. "
                "Refusing to fall back to another chart's janma nakshatra (CR-87)."
            )
        if not moon_sign:
            raise RuntimeError(
                f"ka_sangam: could not resolve Moon sign for chart {chart_id} "
                f"from chart_facts (fact_subject='MOON', fact_key='sign', "
                f"ayanamsha_id='lahiri_chitrapaksha'). "
                "Refusing to fall back to another chart's Moon sign (CR-87)."
            )

        janma_nakshatra_idx = _NAK_NAME_TO_IDX[moon_nakshatra]
        sade_sati_signs    = derive_sade_sati_signs(moon_sign)
        sade_sati_severity = derive_sade_sati_severity(sade_sati_signs)

        location = self._resolve_birth_location(conn, chart_id, birth_params)

        return NativeChartContext(
            janma_nakshatra_idx=janma_nakshatra_idx,
            moon_sign=moon_sign,
            sade_sati_signs=sade_sati_signs,
            sade_sati_severity=sade_sati_severity,
            location=location,
        )

    @staticmethod
    def _resolve_birth_location(conn, chart_id: str, birth_params) -> dict:
        """CR-87: resolve this chart's birth location. Prefers
        ctx.config['birth_params'] (orchestrator-supplied); falls back to a
        direct public.charts query only if birth_params lacks lat/lon. Never
        falls back to Bhubaneswar or any other specific native's coordinates.
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

        # Fallback: query public.charts directly by chart_id (B.10 — never invent).
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
                f"ka_sangam: could not resolve birth location for chart {chart_id} "
                "from ctx.config['birth_params'] or public.charts. Refusing to "
                "fall back to Bhubaneswar or any other chart's coordinates (CR-87)."
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
                f"ka_sangam: could not resolve UTC offset for chart {chart_id}'s "
                f"timezone_id={tzid!r}: {exc}. Refusing to default to IST (CR-87)."
            ) from exc

        return {'lat': float(lat), 'lon': float(lon), 'tz_offset_minutes': tz_offset_minutes}

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
        # JL-014: within-chart relative tier, computed once over this batch's
        # convergence_score distribution (additive to I-21's absolute confidence_label).
        batch_scores = [w.get('convergence_score', 0.0) for w in deduped]
        batch_relative_labels = relative_confidence_labels(batch_scores)
        for w, c_label_relative in zip(deduped, batch_relative_labels):
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
                        horizon_tier, domain,
                        confidence_label_relative, tier_basis
                    ) VALUES (
                        %s, %s, %s, %s,
                        %s::jsonb, %s, NOW(),
                        %s, %s, %s, %s, %s,
                        %s, %s,
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
                        # JL-014: interim within-chart percentile tier + provenance flag
                        c_label_relative,
                        'relative_uncalibrated',
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
