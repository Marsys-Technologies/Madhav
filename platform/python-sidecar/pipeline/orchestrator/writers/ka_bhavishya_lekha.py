"""ka_bhavishya_lekha writer — probabilistic forward projection artifact."""
import json
from datetime import date
from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from brahmagyan.domain_vocabulary import CANONICAL_DOMAINS, CANONICAL_DOMAINS_SORTED


def _reattach_outcome(preserved: dict, signal_id, peak_date) -> tuple:
    """Return `(outcome_recorded, outcome_notes)` for a rebuilt projection row.

    NIRMĀṆA L3-W3. Looks up a previously-recorded outcome by `(signal_id, peak_date)` and
    **consumes** the entry, so anything left in `preserved` after the rebuild is an outcome that
    could not be re-attached — see the check at the end of `run()`.

    Defaults to `(False, None)` — an unmatched projection is a NEW prediction, and giving it
    someone else's outcome would be worse than losing one.
    """
    key = (str(signal_id) if signal_id is not None else None, peak_date)
    return preserved.pop(key, (False, None))


@register('ka_bhavishya_lekha')
class KaBhavishyaLekhaWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # NEVER commit or rollback
        chart_id = ctx.config['chart_id']
        today = date.today()

        # Idempotency
        with conn.cursor() as _timeout_cur:
            _timeout_cur.execute("SET LOCAL statement_timeout = 0")

        # NIRMĀṆA L3-W3 — preserve the P7 falsifiability seam across the rebuild.
        #
        # `outcome_recorded` / `outcome_notes` are the only columns in this table that a WRITER
        # CANNOT REGENERATE: they record what actually happened, which is an observation of the
        # world, not a derivation from L1/L2. The writer used to hardcode `False, None` into every
        # row after a full per-chart DELETE, so the first outcome anyone ever recorded would be
        # destroyed by the next ordinary rebuild, silently.
        #
        # Measured at the time of this fix: 200/200 rows `outcome_recorded = false`, 0 notes — so
        # nothing is lost today and this is purely protective. MACRO_PLAN's P7 is PARKED with the
        # explicit instruction that "nothing in this programme may make the later loop harder";
        # a rebuild that eats outcomes is exactly that.
        #
        # Re-attachment is by `(signal_id, peak_date)` — "a prediction about THIS signal peaking on
        # THIS date" — not by `id` (a sequence, so it changes on every rebuild) and not by
        # `projection_rank` (re-ranking moves it). Conservative on purpose: an outcome is
        # re-attached only on an exact match, never onto a nearby projection.
        preserved_outcomes: dict[tuple, tuple] = {}
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT signal_id, peak_date, outcome_recorded, outcome_notes
                  FROM kala_bhavishya
                 WHERE chart_id = %s
                   AND (outcome_recorded IS TRUE OR outcome_notes IS NOT NULL)
                """,
                (chart_id,),
            )
            for orow in cur.fetchall():
                key = (
                    str(orow['signal_id']) if orow['signal_id'] is not None else None,
                    orow['peak_date'],
                )
                preserved_outcomes[key] = (
                    bool(orow['outcome_recorded']),
                    orow['outcome_notes'],
                )

        with conn.cursor() as cur:
            cur.execute("DELETE FROM kala_bhavishya WHERE chart_id = %s", (chart_id,))

        # Read top-ranked darshana windows in the future (next 5 years).
        # B4-consume: also SELECT kc.domain (added by A3 migration 361).
        # Pre-flight schema probe (read-only, no transaction impact) determines whether
        # the domain column exists. This avoids conn.rollback() which violates the FROZEN
        # orchestrator contract (writers NEVER commit, rollback, or close ctx.db_conn).
        with conn.cursor() as probe_cur:
            probe_cur.execute("""
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'kala_convergence' AND column_name = 'domain'
                LIMIT 1
            """)
            _convergence_has_domain = probe_cur.fetchone() is not None

        domain_select = "kc.domain" if _convergence_has_domain else "NULL AS domain"

        with conn.cursor() as cur:
            cur.execute(f"""
                SELECT kd.convergence_id, kd.signal_id, kd.net_label, kd.effective_score,
                       kd.peak_date, kd.window_start, kd.window_end,
                       kd.narrative, kd.obstruction_summary,
                       kc.confidence_label, kc.rarity_years, kc.mode, kc.tier_basis,
                       {domain_select}
                FROM kala_darshana kd
                JOIN kala_convergence kc ON kd.convergence_id = kc.convergence_id
                WHERE kd.chart_id = %s
                  AND kd.peak_date >= %s
                  AND kd.peak_date <= %s
                  AND kd.net_label NOT IN ('obstructed_severe')
                -- F-BHAV-3 (§N.7 item 2): the old ORDER BY had no tiebreak, so which 100
                -- of the eligible windows survived LIMIT 100 varied build-to-build whenever
                -- effective_score ties (measured: 100/100 rows tied at 0.700 on the
                -- canonical chart). kd.peak_date, kd.convergence_id give a real total order.
                ORDER BY kd.effective_score DESC NULLS LAST, kd.peak_date, kd.convergence_id
                LIMIT 100
            """, (chart_id, today, date(today.year + 5, today.month, today.day)))
            darshana_rows = cur.fetchall()

        if not darshana_rows:
            return WriterResult(asset_id='ka_bhavishya_lekha', rows_inserted=0, notes='No future darshana windows — run ka_kala_darshana first')

        # Store flag on local scope so the loop can access it without a global
        has_domain_col = _convergence_has_domain

        # CF.L3.5: batch-fetch signal_type_id for domain mapping
        # darshana_rows is list[dict] (dict_row cursor); use key access throughout
        signal_ids_seen = [str(r['signal_id']) for r in darshana_rows if r['signal_id']]
        signal_type_map: dict[str, str] = {}
        if signal_ids_seen:
            placeholders = ','.join(['%s'] * len(signal_ids_seen))
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT signal_id, signal_type_id FROM bodha_msr_signals WHERE signal_id IN ({placeholders})",
                    signal_ids_seen,
                )
                for sig_row in cur.fetchall():
                    if sig_row['signal_type_id']:
                        signal_type_map[str(sig_row['signal_id'])] = str(sig_row['signal_type_id'])

        rows = []
        for rank, row in enumerate(darshana_rows, start=1):
            conv_id = row['convergence_id']
            signal_id = row['signal_id']
            net_label = row['net_label']
            eff_score = row['effective_score']
            peak_date = row['peak_date']
            win_start = row['window_start']
            win_end = row['window_end']
            narrative = row['narrative']
            obs_summary = row['obstruction_summary']
            conf_label = row['confidence_label']
            rarity = row['rarity_years']
            mode = row['mode']
            tier_basis = row['tier_basis']

            # Probability tier
            tier = _assign_tier(eff_score, net_label)

            # B4-consume: prefer kc.domain (set by A3 migration 361) over keyword inference.
            # Validate against kala_bhavishya check constraint; fall back to inference if outside allowed set.
            conv_domain = row.get('domain') if has_domain_col else None
            if conv_domain and conv_domain in _ALLOWED_DOMAINS:
                domain = conv_domain
            else:
                domain = _infer_domain(rank, net_label, signal_type_map.get(str(signal_id) if signal_id else ''))

            # Falsifiability hook
            falsifiability = _build_falsifiability(tier, domain, peak_date, eff_score)

            # Source chain
            source_chain = [{'convergence_id': conv_id, 'mode': mode, 'confidence': conf_label}]

            # Projection narrative
            proj_narrative = _build_projection_narrative(
                tier=tier, domain=domain, peak_date=peak_date,
                eff_score=eff_score, conf_label=conf_label,
                rarity=rarity, net_label=net_label, tier_basis=tier_basis,
            )

            rows.append((
                chart_id,
                rank,
                tier,
                domain,
                peak_date.isoformat() if peak_date and hasattr(peak_date, 'isoformat') else None,
                win_start.isoformat() if win_start and hasattr(win_start, 'isoformat') else None,
                win_end.isoformat() if win_end and hasattr(win_end, 'isoformat') else None,
                conv_id,
                signal_id,
                eff_score,
                json.dumps(falsifiability),
                json.dumps(source_chain),
                json.dumps(proj_narrative),
                # L3-W3: carry a recorded outcome across the rebuild rather than resetting it.
                *_reattach_outcome(preserved_outcomes, signal_id, peak_date),
                f"ka_bhavishya_lekha:v1.0:rank={rank}",
            ))

        if rows:
            with conn.cursor() as cur:
                cur.executemany("""
                    INSERT INTO kala_bhavishya (
                        chart_id, projection_rank, probability_tier, domain,
                        peak_date, window_start, window_end,
                        convergence_id, signal_id, effective_score,
                        falsifiability, source_chain, narrative,
                        outcome_recorded, outcome_notes, source_citation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, rows)

        # L3-W3: anything still in `preserved_outcomes` is a recorded observation that this
        # rebuild could not re-attach to any projection — real data about the world that the
        # DELETE above has just removed. Refuse rather than report success: a writer that
        # silently eats an outcome is precisely what the P7 seam must never do, and
        # `WriterResult.notes` is not a signal anything reads (#1738). This cannot fire
        # spuriously today — 200/200 rows carry no outcome — so it costs nothing until it
        # matters, which is the point of putting it in before outcomes start being recorded.
        if preserved_outcomes:
            raise RuntimeError(
                f"ka_bhavishya_lekha: {len(preserved_outcomes)} recorded outcome(s) could not be "
                f"re-attached after the rebuild and would have been destroyed. Unmatched "
                f"(signal_id, peak_date) keys: {sorted(map(str, preserved_outcomes))[:10]}. "
                f"The projections they belong to no longer exist in this build — resolve before "
                f"rebuilding (L3-W3, P7 falsifiability seam)."
            )

        return WriterResult(asset_id='ka_bhavishya_lekha', rows_inserted=len(rows))


def _assign_tier(effective_score: float, net_label: str) -> str:
    """Assign probability tier based on effective score and label."""
    if effective_score is None:
        return 'tier_3_speculative'
    if effective_score >= 0.70 and net_label not in ('obstructed', 'obstructed_severe', 'neutral'):
        return 'tier_1_high'
    if effective_score >= 0.45:
        return 'tier_2_moderate'
    return 'tier_3_speculative'


# SHABDA-SHUDDHI Lane L5 (Fix 1): _DOMAINS imported from the canonical vocabulary module
# (brahmagyan.domain_vocabulary.CANONICAL_DOMAINS). Before this fix the list was hardcoded
# with 'finance' and 'spiritual' — both violate the DB CHECK constraint on kala_bhavishya
# (migration 386), which is why the table was COMPLETELY EMPTY in production.
_DOMAINS = CANONICAL_DOMAINS_SORTED  # all 13 canonical domains, deterministically sorted
_ALLOWED_DOMAINS = CANONICAL_DOMAINS  # mirrors kala_bhavishya_domain_check constraint

# CF.L3.5: keyword sets for signal_type_id → domain mapping.
# Checked in order; first match wins; falls through to 'general'.
# Keys must be canonical domain names (migration 386 CHECK constraint).
_DOMAIN_KEYWORDS: list[tuple[str, list[str]]] = [
    ('career',        ['raja_yoga', 'amatyakaraka', 'tenth', 'karma', 'arudha', 'dasamsha',
                       'profession', 'status', 'power', 'authority']),
    ('relationship',  ['kalatra', 'seventh', 'upapada', 'navamsha', 'spouse', 'partner',
                       'union', 'marriage', 'venus_yoga']),
    ('wealth',        ['dhana', 'second', 'eleventh', 'artha', 'wealth', 'income',
                       'lakshmi', 'kubera', 'dhan']),
    ('health',        ['ayur', 'sixth', 'eighth', 'maraka', 'bala', 'disease',
                       'vitality', 'longevity', 'immunity']),
    ('spirituality',  ['dharma', 'ninth', 'twelfth', 'moksha', 'guru', 'bhakti',
                       'tapas', 'jnana', 'liberation']),
    ('education',     ['vidya', 'fourth', 'fifth', 'learning', 'intellect', 'mercury_yoga',
                       'saraswati', 'knowledge']),
    ('progeny',       ['putra', 'fifth', 'santana', 'children', 'creativity']),
    ('family',        ['fourth', 'matru', 'sukha', 'mother', 'home', 'household']),
    ('residence',     ['fourth', 'property', 'griha', 'bhoomi', 'land', 'building']),
    ('travel',        ['yatra', 'twelfth', 'third', 'foreign', 'journey', 'pilgrimage']),
    ('character',     ['lagna', 'first', 'atmakaraka', 'manas', 'psychology', 'self']),
    ('transition',    ['eighth', 'twelfth', 'sandhi', 'transformation', 'change']),
]


def _infer_domain(rank: int, net_label: str, signal_type_id: str | None = None) -> str:
    """
    CF.L3.5: infer domain from signal_type_id keywords first; rank rotation as fallback.
    """
    if signal_type_id:
        tid_lower = signal_type_id.lower()
        for domain, keywords in _DOMAIN_KEYWORDS:
            if any(kw in tid_lower for kw in keywords):
                return domain
    # Domain rotation removed: produces false-precision labels violating MACRO_PLAN ethical
    # framework (calibrated/falsifiable outputs). Unclassified signals use 'general'.
    return 'general'


def _build_falsifiability(tier: str, domain: str, peak_date, eff_score: float) -> dict:
    """Build falsifiability hooks for this projection."""
    peak_str = str(peak_date) if peak_date else 'the projected window'

    # SHABDA-SHUDDHI R7: canonical 13-domain vocabulary, no legacy keys.
    domain_confirms = {
        'career': 'significant career event (new role, promotion, venture launch, client gain)',
        'health': 'notable health event (condition onset, recovery milestone, medical event)',
        'relationship': 'significant relational event (union, separation, new connection)',
        'wealth': 'measurable financial event (income jump, loss, investment event)',
        'spirituality': 'notable spiritual shift (practice deepening, teacher encounter, insight)',
        'education': 'educational milestone (enrollment, completion, certification)',
        'progeny': 'progeny-related event (conception, birth, child milestone)',
        'family': 'family event (parental milestone, household change)',
        'residence': 'property/residence event (move, purchase, renovation)',
        'travel': 'travel event (relocation, foreign settlement, significant journey)',
        'character': 'personal transformation (mindset shift, psychological change)',
        'transition': 'life transition (phase change, significant endings/beginnings)',
        'general': 'notable life event (legal matter, public recognition, general milestone)',
    }

    confirm = f"Observable within ±21 days of {peak_str}: {domain_confirms.get(domain, 'notable life event')}"
    deny = f"No observable {domain} event within ±21 days of {peak_str} despite favorable circumstances"
    eval_date = str(peak_date) if peak_date else 'peak_date'

    return {
        'confirm_observable': confirm,
        'deny_observable': deny,
        'evaluation_date': eval_date,
        'evaluation_window_days': 21,
    }


# F-BHAV-2 (§N.7 items 5/6, MACRO_PLAN Ethical Framework): these labels used to read
# "High probability (>=70% convergence, clear activation)" — reading a [0,1] structural
# score as a calibrated percentage is a category error. `effective_score` is a product of
# catalog constants (ka_kala_darshana's convergence x obstruction terms), not a probability
# estimate; wording it as one over a substrate whose OWN `kala_convergence.tier_basis`
# column stamps itself 'relative_uncalibrated' (100% of rows, measured) is exactly the
# defect this doctrine item exists to close. Reworded to describe structural convergence
# strength, never "probability" or "%".
_TIER_LABELS = {
    'tier_1_high': 'High structural convergence (score >=0.70, clear activation)',
    'tier_2_moderate': 'Moderate structural convergence (score 0.45-0.70)',
    'tier_3_speculative': 'Speculative (score <0.45 or obstructed)',
}

# The only `kala_convergence.tier_basis` value that would license "calibrated probability"
# language — none observed in production (100% 'relative_uncalibrated', measured). Kept as
# an explicit allowlist rather than an "!= 'relative_uncalibrated'" exclusion so a future,
# genuinely-unrecognized tier_basis value defaults to the SAFER, less-confident wording
# (§N.7 item 6: an honest null/uncertain framing beats an invented favorable one).
_CALIBRATED_TIER_BASES = frozenset({'calibrated'})


def _build_projection_narrative(tier: str, domain: str, peak_date, eff_score: float,
                                conf_label: str, rarity: float, net_label: str,
                                tier_basis: str | None) -> dict:
    peak_str = str(peak_date) if peak_date else 'unknown date'
    tier_desc = _TIER_LABELS.get(tier, tier)
    rarity_str = f"{rarity:.1f}-year cycle" if rarity else "event"

    headline = f"{domain.capitalize()} activation near {peak_str}"
    prob_stmt = (
        f"{tier_desc}. Effective convergence: {eff_score:.2f}. "
        f"Confidence: {conf_label or 'speculative'}."
    )
    domain_ctx = f"Domain: {domain}. Cycle type: {rarity_str}."

    if tier_basis in _CALIBRATED_TIER_BASES:
        caveat = (
            "This projection reflects a calibrated probability estimate. "
            "Record actual outcomes at evaluation_date for calibration refinement."
        )
    else:
        caveat = (
            "This projection is a structural, uncalibrated prior — a computed convergence "
            f"strength score (kala_convergence.tier_basis={tier_basis!r}), not a calibrated "
            "probability estimate. Record actual outcomes at evaluation_date to build the "
            "calibration data this projection does not yet have."
        )

    return {
        'headline': headline,
        'probability_statement': prob_stmt,
        'domain_context': domain_ctx,
        'caveat': caveat,
    }
