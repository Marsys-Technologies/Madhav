"""
ka_yojaka writer — activation-predicate bridge (L3 K3)
FROZEN orchestrator contract: @register, run(ctx) -> WriterResult
Orchestrator owns the transaction — writer must NOT commit or rollback
NEVER writes to any bodha_* table

D6 (Kāla completeness v2): reads bodha_cgm_nodes pagerank centrality and
bodha_cdlm_cells domain-link strength to enrich each predicate's
dasha_eligibility_rule with a cgm_centrality_weight field. This allows
ka_sangam to prioritize predicates whose primary graha is a graph hub.

CR-37 (SARVA-SIDDHI W-1 T-3): YOGA/DOSHA activation dating. The ratified
binder set no usable constituent_lords for yoga_label / dosha signals (it
dumped L1 fact-id hashes — see binder._extract_constituent_lords), so those
predicates never matched a daśā period and came out UNDATED. This writer now
resolves the REAL forming grahā(s) from authoritative L1 sources:
  • YOGA — `ga_yoga_firings.constituent_planets` keyed by yoga_canonical_id
    (mapped from the signal's yoga_label constituent fact). A Nabhasa/ākṛti
    "distribution" yoga (formed by (near-)all seven grahas) has no single
    activating daśā lord and stays honestly UNDATED with an inspectable
    `always_on_reason` (§N.6); a bounded-set yoga (Pañca-Mahāpuruṣa, solar/
    lunar adjacency, Rāja/Dhana) inherits its forming grahas → real windows.
  • DOSHA — kāla-sarpa (fired) activates through the nodal axis [Rahu, Ketu]
    (definitional); a fired dosha_label inherits the grahā(s) named by its
    graha_position constituent facts. Unfired / requires_pass catalog-only
    doshas stay UNDATED (dating a catalog-only match would be fabrication).
Every emitted lord traces to a real L1 row (§N.5 — reference, never invent).
"""
import json
import logging

from pipeline.orchestrator.writers import WriterBase, WriterResult, register
from services.ka_yojaka.classifier import classify_signal
from services.ka_yojaka.binder import build_predicate
from services.ka_temporal import (
    extract_lords_from_config,
    extract_lords_from_text,
    lord_from_house_varga,
    normalize_graha,
)

logger = logging.getLogger(__name__)

# CR-37: a Nabhasa/ākṛti/saṅkhyā "distribution" yoga is defined by how (near-)all
# seven grahas are arranged (e.g. Gola/Kedāra/Yuga/Śūla — the "how many signs the
# 7 planets occupy" saṅkhyā family, and the ākṛti shape yogas). Every graha is a
# constituent, so no single daśā lord discriminates its activation — dating it to
# "the current daśā" would manufacture a discrete window for an always-on natal
# condition (fabrication). Point yogas name a bounded forming set: Pañca-
# Mahāpuruṣa = 1, solar/lunar adjacency (Vasi/Veśi/Anaphā) = 2-3, Rāja/Dhana/
# NBRY = 2-5. A threshold of 6 cleanly separates the two on the observed data.
DISTRIBUTION_YOGA_MIN_GRAHAS = 6


@register('ka_yojaka')
class KaYojakaWriter(WriterBase):
    def run(self, ctx) -> WriterResult:
        conn = ctx.db_conn  # orchestrator owns the transaction; writer never commits
        chart_id = ctx.config['chart_id']

        # Step 1: delete existing for this chart (delete-then-insert idempotency per §N.3)
        with conn.cursor() as _timeout_cur:
            _timeout_cur.execute("SET LOCAL statement_timeout = 0")
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_activation_predicates WHERE chart_id = %s",
                (chart_id,),
            )

        # Step 2: read all MSR signals for this chart (SELECT only — never write to bodha_*)
        # WP-S4-R45/CR-5/CR-12/CR-48: shadbala_norm added — real per-signal strength
        # feeding the non-affliction proxy below (kills the flat-0.5 alignment wall).
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT signal_id, chart_id, ayanamsha_id, signal_type_class, signal_type_id,
                       configuration_jsonb, constituent_facts_array, valence, dignity_score,
                       shadbala_norm
                FROM bodha_msr_signals WHERE chart_id = %s
                """,
                (chart_id,),
            )
            signals = cur.fetchall()

        # CR-5/CR-12/CR-48 (flat dasha_activation_proximity_score=0.5 wall): the
        # writer's downstream _proximity_score() formula (dignity * non_affliction)
        # was ALWAYS collapsing to exactly 0.5 because strength_affliction_hook
        # only ever carried the STRING label 'scale_by': 'dignity_score' — never
        # an actual number under either 'dignity_score' or 'non_affliction' keys —
        # so both factors silently hit their defaults (0.5 * 1.0 = 0.5) on every
        # one of 49,315 rows for 482012f1 (verified live). Fix: propagate the
        # REAL per-signal bodha_msr_signals.dignity_score and a chart-normalized
        # shadbala_norm (min-max, same normalization idiom as the CGM/CDLM
        # prefetches above) as the actual dignity/non_affliction numbers the
        # formula reads. No fabrication — both source columns are already
        # L2-computed; this only stops dropping them on the floor.
        _shadbala_vals = [
            float(s['shadbala_norm']) for s in signals
            if s.get('shadbala_norm') is not None
        ]
        max_shadbala = max(_shadbala_vals) if _shadbala_vals else 1.0
        if max_shadbala <= 0:
            max_shadbala = 1.0

        # D6: pre-fetch CGM centrality (pagerank) by node_subject for this chart.
        # Used to add cgm_centrality_weight to each predicate's dasha_eligibility_rule.
        cgm_pagerank: dict[str, float] = self._fetch_cgm_pagerank(conn, chart_id)

        # D6: pre-fetch CDLM domain strengths for this chart (domain → link_strength).
        cdlm_domain_strength: dict[str, float] = self._fetch_cdlm_domain_strength(conn, chart_id)

        # WP-S4-R45-iter2: pre-fetch the (ayanamsha, varga, house) -> bhava-lord
        # map from L1 chart_facts. Used as the SECOND lord-resolution fallback
        # (after extract_lords_from_config) for SUBSYSTEM/composite_state
        # predicates whose configuration_jsonb carries `house` (int) + `varga`
        # (e.g. "D9") but no direct graha key — net_argala_per_varga and
        # siblings. §N.5-clean: every lord traces to a real L1 fact row.
        house_lord_map: dict[tuple, str] = self._fetch_house_lord_map(conn, chart_id)

        # CR-37: authoritative YOGA/DOSHA forming-graha sources.
        #  - yoga_firing_planets: {(ayanamsha_id, yoga_canonical_id): [planet,...]}
        #    from L1 ga_yoga_firings (fired yogas only).
        #  - activation_source_facts: {fact_id: (fact_category, fact_subject)} for
        #    the yoga_label / dosha_label / graha_position facts used to map a
        #    signal → its yoga canonical id (yoga) or forming grahas (dosha).
        yoga_firing_planets: dict[tuple, list] = self._fetch_yoga_firing_planets(conn, chart_id)
        activation_source_facts: dict[str, tuple] = self._fetch_activation_source_facts(conn, chart_id)

        # Step 3a: pratijna linkage — promise-register IDs per domain + multi-system confirmation
        # SAVEPOINT-guarded: soft dependency on P3B data (bodha_pratijna may not be built yet)
        pratijna_by_domain: dict[str, list[str]] = {}
        domain_confirmation: dict[str, int] = {}
        with conn.cursor() as _sp:
            _sp.execute("SAVEPOINT sp_pratijna_yojaka")
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT bp.pratijna_id, beo.domain
                    FROM bodha_pratijna bp
                    JOIN brahma_event_ontology beo USING (event_class_id)
                    WHERE bp.chart_id = %s AND bp.status IN ('promised', 'conditional')
                    ORDER BY bp.grade DESC
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    d = str(row['domain'] or 'unknown')
                    pratijna_by_domain.setdefault(d, []).append(str(row['pratijna_id']))
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT beo.domain, COUNT(DISTINCT bp.ayanamsha_id) AS aya_count
                    FROM bodha_pratijna bp
                    JOIN brahma_event_ontology beo USING (event_class_id)
                    WHERE bp.chart_id = %s AND bp.status = 'promised'
                    GROUP BY beo.domain
                    """,
                    (chart_id,),
                )
                for row in cur.fetchall():
                    domain_confirmation[str(row['domain'])] = int(row['aya_count'] or 0)
            with conn.cursor() as _sp:
                _sp.execute("RELEASE SAVEPOINT sp_pratijna_yojaka")
            logger.debug("ka_yojaka: pratijna linkage loaded — %d domains", len(pratijna_by_domain))
        except Exception as _exc:
            with conn.cursor() as _sp:
                _sp.execute("ROLLBACK TO SAVEPOINT sp_pratijna_yojaka")
            logger.debug("ka_yojaka: pratijna linkage skipped: %s", _exc)

        # Step 3: classify + bind each signal
        # Connection uses dict_row factory — access columns by name, not integer index.
        # Two-pass: pass 1 resolves lords via config keys + house/varga (both
        # in-memory); anything still unresolved is queued for pass 2's single
        # batched fact_subject lookup (WP-S4-R45-iter2) rather than N+1 queries.
        enriched = []  # list of (sig, sc, pred)
        needs_fact_subject: list[tuple[int, str]] = []  # (index into enriched, fact_id)
        for sig in signals:
            signal_dict = {
                'signal_id': sig['signal_id'],
                'chart_id': sig['chart_id'],
                'ayanamsha_id': sig['ayanamsha_id'],
                'signal_type_class': sig['signal_type_class'],
                'signal_type_id': sig['signal_type_id'],
                'configuration_jsonb': sig['configuration_jsonb'],
                'constituent_facts_array': sig['constituent_facts_array'],
                'valence': sig['valence'],
                'dignity_score': sig['dignity_score'],
                'shadbala_norm': sig.get('shadbala_norm'),
            }
            sc = classify_signal(signal_dict)
            pred = build_predicate(signal_dict, sc)

            # CR-5/CR-12/CR-48: feed the REAL per-signal dignity_score /
            # normalized shadbala into strength_affliction_hook so
            # date_resolver._proximity_score's dignity*non_affliction formula
            # stops defaulting to 0.5*1.0 on every row (see prefetch note above).
            if signal_dict['dignity_score'] is not None:
                pred['strength_affliction_hook']['dignity_score'] = round(float(signal_dict['dignity_score']), 4)
            if signal_dict['shadbala_norm'] is not None:
                pred['strength_affliction_hook']['non_affliction'] = round(
                    min(1.0, max(0.0, float(signal_dict['shadbala_norm']) / max_shadbala)), 4
                )

            # WP-2.1 / R-45 (LANE0 root cause): the ratified binder only set
            # concrete `constituent_lords` for the YOGA class, so ~99% of
            # predicates carried no lord for ka_kalasutra to resolve a daśā
            # window against → NULL activation dates. Enrich EVERY predicate
            # with the grahā(s) whose daśā activates the signal, extracted
            # deterministically from the signal's configuration (graha keys,
            # rāśi-lordship of sign keys, sāḍe-sātī→Śani). Fills only when the
            # ratified template did not already supply concrete lords; never
            # overwrites the frozen template semantics (same enrichment pattern
            # as the D6 / P5A additions below).
            existing_lords = pred['dasha_eligibility_rule'].get('constituent_lords') or []
            config = signal_dict.get('configuration_jsonb')
            if isinstance(config, str):
                import json as _json
                try:
                    config = _json.loads(config)
                except Exception:
                    config = {}
            config = config or {}

            # CR-37: authoritative YOGA/DOSHA forming-graha resolution. Runs
            # BEFORE the generic config/house/fact_subject chain and OVERRIDES
            # whatever the binder produced for these classes, because the L1
            # firing sources are the authority (§N.5). For a distribution yoga
            # it sets no lords and stamps always_on_reason (stays honestly
            # undated); for a bounded-set yoga / fired dosha it sets the real
            # forming grahas so the resolver produces genuine daśā windows.
            if sc in ('YOGA', 'DOSHA'):
                firing_lords, always_on_reason, firing_source = _resolve_firing_lords(
                    signal_dict, sc, config, yoga_firing_planets, activation_source_facts,
                )
                if always_on_reason:
                    pred['dasha_eligibility_rule']['constituent_lords'] = []
                    pred['dasha_eligibility_rule']['always_on_reason'] = always_on_reason
                    pred['dasha_eligibility_rule']['constituent_lords_source'] = firing_source
                    existing_lords = []
                elif firing_lords:
                    pred['dasha_eligibility_rule']['constituent_lords'] = firing_lords
                    pred['dasha_eligibility_rule']['constituent_lords_source'] = firing_source
                    existing_lords = firing_lords

            if not existing_lords:
                resolved_lords = extract_lords_from_config(
                    config,
                    signal_type_id=signal_dict.get('signal_type_id'),
                    signal_type_class=signal_dict.get('signal_type_class'),
                )
                if resolved_lords:
                    pred['dasha_eligibility_rule']['constituent_lords'] = resolved_lords
                    pred['dasha_eligibility_rule']['constituent_lords_source'] = 'ka_yojaka:extract_lords_from_config'
                    existing_lords = resolved_lords

            # WP-S4-R45-iter2 fallback #2: SUBSYSTEM/composite_state predicates
            # (net_argala_per_varga and siblings) carry `house` (int) + `varga`
            # ("D9") in configuration_jsonb but no direct graha key — the house
            # is the signal's subject, its BHAVA LORD is the activating lord.
            # Resolved from the L1 lord_in_house_per_varga fact via the
            # prefetched map — no fabrication, real chart_facts row.
            if not existing_lords and 'house' in config and 'varga' in config:
                house_lord = lord_from_house_varga(
                    house_lord_map, signal_dict.get('ayanamsha_id'),
                    config.get('varga'), config.get('house'),
                )
                if house_lord:
                    pred['dasha_eligibility_rule']['constituent_lords'] = [house_lord]
                    pred['dasha_eligibility_rule']['constituent_lords_source'] = 'ka_yojaka:house_varga_bhava_lord'
                    existing_lords = [house_lord]

            # D6: enrich dasha_eligibility_rule with CGM centrality weight.
            # Primary graha is the planet most likely to be the graph node subject.
            primary_graha = _extract_primary_graha(signal_dict)
            cgm_weight = cgm_pagerank.get(primary_graha, 0.5) if primary_graha else 0.5
            pred['dasha_eligibility_rule']['cgm_centrality_weight'] = round(cgm_weight, 4)

            # D6: enrich with CDLM domain strength for the signal's inferred domain.
            domain = _infer_signal_domain(signal_dict)
            pred['dasha_eligibility_rule']['cdlm_domain_strength'] = round(
                cdlm_domain_strength.get(domain, 0.5), 4
            )

            # P5A: pratijna linkage — activated promise IDs + multi-system ayanamsha confirmation count
            pred['dasha_eligibility_rule']['pratijna_ids'] = pratijna_by_domain.get(domain, [])[:5]
            pred['dasha_eligibility_rule']['multi_system_confirmation_count'] = domain_confirmation.get(domain, 0)

            idx = len(enriched)
            enriched.append((sig, sc, pred))

            # WP-S4-R45-iter2 fallback #3 (queued): still no lord, but the
            # signal references an L1 chart_facts row — queue its fact_id for
            # a single batched fact_subject lookup after this loop (avoids
            # N+1 queries across ~20K+ predicates).
            if not existing_lords:
                facts = signal_dict.get('constituent_facts_array') or []
                if facts:
                    needs_fact_subject.append((idx, str(facts[0])))

        # Fallback #3: one batched query for every queued fact_id, then a
        # cheap in-memory second pass via extract_lords_from_text (§N.5 —
        # every recovered lord traces to a real chart_facts.fact_subject).
        if needs_fact_subject:
            fact_ids = list({fid for _, fid in needs_fact_subject})
            subject_by_fact_id = self._fetch_fact_subjects(conn, fact_ids)
            for idx, fid in needs_fact_subject:
                subject = subject_by_fact_id.get(fid)
                if not subject:
                    continue
                lords = extract_lords_from_text(subject)
                if lords:
                    _sig, _sc, pred = enriched[idx]
                    pred['dasha_eligibility_rule']['constituent_lords'] = lords
                    pred['dasha_eligibility_rule']['constituent_lords_source'] = 'ka_yojaka:fact_subject_tokens'

        rows = []
        for sig, sc, pred in enriched:
            rows.append((
                str(sig['chart_id']),
                str(sig['ayanamsha_id']),
                str(sig['signal_id']),
                sc,
                json.dumps(pred['dasha_eligibility_rule']),
                json.dumps(pred['transit_trigger']),
                json.dumps(pred['strength_affliction_hook']),
                json.dumps(pred['derivation_ledger']),
            ))

        # Step 4: batch insert (1000 rows per batch)
        # psycopg3 executemany: standard VALUES (%s, ...) form, delete-then-insert idempotency per §N.3
        _INSERT_SQL = """
            INSERT INTO kala_activation_predicates
                (chart_id, ayanamsha_id, signal_id, signature_class,
                 dasha_eligibility_rule_jsonb, transit_trigger_jsonb,
                 strength_affliction_hook_jsonb, derivation_ledger_jsonb)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """
        with conn.cursor() as cur:
            for i in range(0, len(rows), 1000):
                batch = rows[i:i + 1000]
                cur.executemany(_INSERT_SQL, batch)

        return WriterResult(asset_id='ka_yojaka', rows_inserted=len(rows))

    def _fetch_house_lord_map(self, conn, chart_id: str) -> dict:
        """WP-S4-R45-iter2: fetch chart_facts(fact_category='lord_in_house_per_varga')
        and build {(ayanamsha_id, "{varga}_H{house}"): lord_name}. Rows are
        shaped fact_subject="D9_H1", fact_value_text="Mars_in_H12" (the lord
        OF D9-H1 IS Mars — the "_in_H12" suffix is where that lord currently
        sits, irrelevant here; only the prefix is the lord name). SAVEPOINT-
        guarded soft dependency (per _fetch_cgm_pagerank's pattern) — returns
        {} on any failure rather than aborting the writer's transaction.
        """
        result: dict = {}
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_house_lord")
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ayanamsha_id, fact_subject, fact_value_text
                    FROM chart_facts
                    WHERE chart_id = %s AND fact_category = 'lord_in_house_per_varga'
                      AND fact_value_text IS NOT NULL
                    """,
                    (chart_id,),
                )
                rows = cur.fetchall()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_house_lord")
            for r in rows:
                lord = str(r['fact_value_text']).split('_in_')[0]
                if lord:
                    result[(str(r['ayanamsha_id']), str(r['fact_subject']))] = lord
            logger.debug("ka_yojaka: house-lord map loaded — %d entries", len(result))
        except Exception as exc:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_house_lord")
            logger.debug("ka_yojaka: house-lord map fetch skipped: %s", exc)
        return result

    def _fetch_fact_subjects(self, conn, fact_ids: list) -> dict:
        """WP-S4-R45-iter2: batch-fetch fact_subject for a list of chart_facts
        fact_ids (the last-resort fallback #3 source). One query for the whole
        chart rather than N+1. SAVEPOINT-guarded soft dependency.
        """
        result: dict = {}
        if not fact_ids:
            return result
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_fact_subjects")
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT fact_id, fact_subject FROM chart_facts WHERE fact_id = ANY(%s)",
                    (fact_ids,),
                )
                rows = cur.fetchall()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_fact_subjects")
            for r in rows:
                result[str(r['fact_id'])] = r['fact_subject']
            logger.debug("ka_yojaka: fact_subject batch loaded — %d/%d resolved", len(result), len(fact_ids))
        except Exception as exc:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_fact_subjects")
            logger.debug("ka_yojaka: fact_subject batch fetch skipped: %s", exc)
        return result

    def _fetch_cgm_pagerank(self, conn, chart_id: str) -> dict[str, float]:
        """
        Fetch CGM node pagerank scores keyed by node_subject (graha name / bhava label).
        Normalizes scores to [0, 1] relative to the chart's max pagerank.
        Returns empty dict on failure (soft dependency — CGM may not be built yet).
        """
        result: dict[str, float] = {}
        # SAVEPOINT so a query failure (e.g. a schema drift) rolls back ONLY this soft
        # lookup. Without it, a failed SELECT aborts the writer's whole transaction and the
        # later batch INSERT dies with InFailedSqlTransaction (the bug that left
        # kala_activation_predicates empty and cascaded through all of Kāla/Phala/Mīmāṃsā).
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_cgm")
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT node_subject, COALESCE(pagerank_score::float, 0.5) AS pgr
                    FROM bodha_cgm_nodes
                    WHERE chart_id = %s AND pagerank_score IS NOT NULL
                    ORDER BY pagerank_score DESC
                    """,
                    (chart_id,),
                )
                rows = cur.fetchall()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_cgm")
            if not rows:
                return result
            max_pgr = max(float(r['pgr']) for r in rows) or 1.0
            for r in rows:
                result[str(r['node_subject'])] = min(1.0, float(r['pgr']) / max_pgr)
            logger.debug("ka_yojaka: CGM centrality loaded — %d nodes", len(result))
        except Exception as exc:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_cgm")
            logger.debug("ka_yojaka: CGM pagerank fetch skipped: %s", exc)
        return result

    def _fetch_cdlm_domain_strength(self, conn, chart_id: str) -> dict[str, float]:
        """
        Fetch average CDLM net linkage strength per domain from bodha_cdlm_cells,
        normalized to [0, 1] relative to the strongest domain. Returns
        {domain_name: weight} for predicate enrichment. SAVEPOINT-guarded soft lookup.
        """
        result: dict[str, float] = {}
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_cdlm")
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT domain_row AS domain, AVG(net_linkage_strength::float) AS avg_strength
                    FROM bodha_cdlm_cells
                    WHERE chart_id = %s AND net_linkage_strength IS NOT NULL
                    GROUP BY domain_row
                    """,
                    (chart_id,),
                )
                rows = cur.fetchall()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_cdlm")
            if not rows:
                return result
            max_strength = max(float(r['avg_strength']) for r in rows) or 1.0
            for r in rows:
                result[str(r['domain']).lower()] = min(1.0, max(0.0, float(r['avg_strength']) / max_strength))
            logger.debug("ka_yojaka: CDLM domain strengths loaded — %d domains", len(result))
        except Exception as exc:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_cdlm")
            logger.debug("ka_yojaka: CDLM domain strength fetch skipped: %s", exc)
        return result


    def _fetch_yoga_firing_planets(self, conn, chart_id: str) -> dict[tuple, list]:
        """CR-37: authoritative forming-graha set per FIRED yoga from L1
        ga_yoga_firings. Returns {(ayanamsha_id, yoga_canonical_id): [planet,...]}.
        SAVEPOINT-guarded soft dependency (same pattern as _fetch_cgm_pagerank) —
        returns {} on any failure rather than aborting the writer's transaction.
        """
        result: dict[tuple, list] = {}
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_yoga_firings")
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT ayanamsha_id, yoga_canonical_id, constituent_planets
                    FROM ga_yoga_firings
                    WHERE chart_id = %s AND fired = true
                      AND constituent_planets IS NOT NULL
                    """,
                    (chart_id,),
                )
                rows = cur.fetchall()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_yoga_firings")
            for r in rows:
                planets = r['constituent_planets']
                if isinstance(planets, str):
                    try:
                        planets = json.loads(planets)
                    except Exception:
                        continue
                if isinstance(planets, list) and planets:
                    result[(str(r['ayanamsha_id']), str(r['yoga_canonical_id']))] = [
                        str(p) for p in planets
                    ]
            logger.debug("ka_yojaka: yoga firing planets loaded — %d fired yogas", len(result))
        except Exception as exc:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_yoga_firings")
            logger.debug("ka_yojaka: yoga firing planets fetch skipped: %s", exc)
        return result

    def _fetch_activation_source_facts(self, conn, chart_id: str) -> dict[str, tuple]:
        """CR-37: {fact_id: (fact_category, fact_subject)} for the L1 chart_facts
        categories used to resolve yoga/dosha forming grahas — 'yoga_label' &
        'dosha_label' (fact_subject IS the canonical id), and 'graha_position'
        (fact_subject IS the graha). SAVEPOINT-guarded soft dependency.
        """
        result: dict[str, tuple] = {}
        with conn.cursor() as sp:
            sp.execute("SAVEPOINT sp_activation_facts")
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT fact_id, fact_category, fact_subject
                    FROM chart_facts
                    WHERE chart_id = %s
                      AND fact_category IN ('yoga_label', 'dosha_label', 'graha_position')
                    """,
                    (chart_id,),
                )
                rows = cur.fetchall()
            with conn.cursor() as sp:
                sp.execute("RELEASE SAVEPOINT sp_activation_facts")
            for r in rows:
                result[str(r['fact_id'])] = (str(r['fact_category']), r['fact_subject'])
            logger.debug("ka_yojaka: activation source facts loaded — %d facts", len(result))
        except Exception as exc:
            with conn.cursor() as sp:
                sp.execute("ROLLBACK TO SAVEPOINT sp_activation_facts")
            logger.debug("ka_yojaka: activation source facts fetch skipped: %s", exc)
        return result


# ── D6 helpers (module-level) ─────────────────────────────────────────────────

# CR-85 (D-2 Lane V-4): centrality-consumption stub removal, bounded to this
# one normalization fix — nothing else in ka_yojaka touched (D-3 owns the full
# convergence engine). Root cause of the flat-0.5 cgm_centrality_weight (live-
# probed at BIND_D-2.md §B.1 check 5 before this fix): _fetch_cgm_pagerank
# keys its lookup by bodha_cgm_nodes.node_subject, which bo_bimba writes in
# Title Case ('Mars', 'Rahu', …) — but this function returned the RAW
# configuration_jsonb value verbatim (often 'MAR', 'mars', 'RAH_MEAN', or a
# 2-char L1 code), so `cgm_pagerank.get(primary_graha, 0.5)` almost always
# missed the dict and silently fell back to the 0.5 default for nearly every
# predicate. Fix: normalize through the SAME Title-Case map bo_bimba/
# bo_karanajala already use as the CGM node_subject convention, so a real hit
# — not the 0.5 stub — is the common case.
_GRAHA_CODE_TO_TITLE: dict[str, str] = {
    "SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MARS": "Mars",
    "MER": "Mercury", "MERCURY": "Mercury", "JUP": "Jupiter", "JUPITER": "Jupiter",
    "VEN": "Venus", "VENUS": "Venus", "SAT": "Saturn", "SATURN": "Saturn",
    "RAH": "Rahu", "RAH_MEAN": "Rahu", "RAHU": "Rahu",
    "KET": "Ketu", "KET_MEAN": "Ketu", "KETU": "Ketu",
}


def _normalize_graha_to_node_subject(raw: str) -> str | None:
    """Any graha token (2/3-letter L1 code, upper/lower/mixed case full name)
    -> the exact Title-Case form bodha_cgm_nodes.node_subject stores for
    node_type='graha' (bo_bimba._SUBJECT_TO_GRAHA's convention)."""
    if not raw or not isinstance(raw, str):
        return None
    key = raw.strip().upper()
    if key in _GRAHA_CODE_TO_TITLE:
        return _GRAHA_CODE_TO_TITLE[key]
    title = raw.strip().title()
    return title if title in _GRAHA_CODE_TO_TITLE.values() else None


def _extract_primary_graha(signal_dict: dict) -> str | None:
    """Extract the primary graha name from a signal's configuration_jsonb,
    normalized to the CGM node_subject convention (CR-85)."""
    cfg = signal_dict.get('configuration_jsonb') or {}
    if isinstance(cfg, str):
        import json as _json
        try:
            cfg = _json.loads(cfg)
        except Exception:
            return None
    # Try common keys where planet name appears
    for key in ('fact_value_text', 'primary_graha', 'graha', 'planet', 'lord'):
        val = cfg.get(key)
        if val and isinstance(val, str):
            normalized = _normalize_graha_to_node_subject(val)
            if normalized:
                return normalized
    return None


_SIGNAL_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    'career':       ['raja', 'karma', 'tenth', 'arudha', 'amatyakaraka', 'profession'],
    'relationship': ['kalatra', 'seventh', 'navamsha', 'spouse', 'venus', 'upapada'],
    'finance':      ['dhana', 'second', 'eleventh', 'wealth', 'lakshmi', 'artha'],
    'health':       ['ayur', 'sixth', 'eighth', 'maraka', 'vitality', 'disease'],
    'spiritual':    ['dharma', 'ninth', 'twelfth', 'moksha', 'guru', 'liberation'],
    'education':    ['vidya', 'fourth', 'fifth', 'mercury', 'saraswati', 'learning'],
}


def _infer_signal_domain(signal_dict: dict) -> str:
    """Infer a signal's domain from signal_type_id for CDLM strength lookup."""
    stid = (signal_dict.get('signal_type_id') or '').lower()
    for domain, keywords in _SIGNAL_DOMAIN_KEYWORDS.items():
        if any(kw in stid for kw in keywords):
            return domain
    return 'general'


def _resolve_firing_lords(
    signal_dict: dict,
    signature_class: str,
    config: dict,
    yoga_firing_planets: dict,
    activation_source_facts: dict,
) -> tuple[list, str | None, str | None]:
    """CR-37: authoritative forming-graha resolution for one YOGA/DOSHA signal.

    Returns (lords, always_on_reason, source):
      • lords            — canonical graha names whose daśā activates the signal
                           (empty when none resolve or the yoga is always-on).
      • always_on_reason — set ONLY for a Nabhasa/ākṛti distribution yoga; the
                           caller then leaves it undated with this inspectable
                           reason (§N.6). None otherwise.
      • source           — provenance label for constituent_lords_source.

    Never fabricates: a value is returned only when a real L1 row backs it.
    Unfired / requires_pass catalog-only doshas resolve to ([], None, None) —
    correctly undated.
    """
    ayan = str(signal_dict.get('ayanamsha_id'))
    cfa = signal_dict.get('constituent_facts_array') or []
    if not isinstance(cfa, list):
        cfa = []

    if signature_class == 'YOGA':
        # Nabhasa saṅkhyā "distribution" yogas (Gola/Yuga/Śūla/Kedāra/Pāśa/…)
        # are defined by how many SIGNS the seven grahas occupy — their bodha
        # fire_reason is the '<N>_distinct_signs' condition. Every graha is a
        # constituent, so no single daśā lord discriminates activation → the
        # yoga is honestly UNDATED with an inspectable reason (§N.6), never a
        # manufactured window. Checked FIRST because the L1 ga_yoga_firings
        # engine does not record every saṅkhyā yoga (e.g. Gola/Śūla/Yuga on the
        # native), and the lookup below would otherwise leave them silently null.
        fire_reason = str((config or {}).get('fire_reason') or '')
        if fire_reason.endswith('distinct_signs'):
            return [], 'distribution_yoga_sankhya', 'ka_yojaka:sankhya_fire_reason'

        # Map the signal → its yoga canonical id via a yoga_label constituent
        # fact (fact_subject IS the canonical id), then look up the fired yoga's
        # complete forming-graha set from L1 ga_yoga_firings.
        for fid in cfa:
            cat, subj = activation_source_facts.get(str(fid), (None, None))
            if cat != 'yoga_label' or not subj:
                continue
            planets = yoga_firing_planets.get((ayan, str(subj)))
            if not planets:
                continue
            if len(planets) >= DISTRIBUTION_YOGA_MIN_GRAHAS:
                return [], 'distribution_yoga_all_grahas', 'ka_yojaka:ga_yoga_firings'
            lords: list[str] = []
            for p in planets:
                g = normalize_graha(p)
                if g and g not in lords:
                    lords.append(g)
            if lords:
                return lords, None, 'ka_yojaka:ga_yoga_firings'
        return [], None, None

    # DOSHA
    stid = str(signal_dict.get('signal_type_id') or '')
    fires = config.get('fires')
    fires_true = fires is True or str(fires).strip().lower() == 'true'

    if stid.startswith('kala_sarpa'):
        # Kāla-sarpa: all grahas hemmed within the Rāhu-Ketu axis; it operates
        # through the nodal daśās by definition. Only a FIRED per-varga detection
        # is a real dosha — a 'none' variant carries no dosha to activate.
        if fires_true:
            return ['Rahu', 'Ketu'], None, 'ka_yojaka:kala_sarpa_nodal_axis'
        return [], None, None

    if fires_true:
        # A confirmed dosha inherits the grahā(s) named by its graha_position
        # constituent facts (e.g. Kemadruma → Moon). §N.5 — real L1 rows.
        lords = []
        for fid in cfa:
            cat, subj = activation_source_facts.get(str(fid), (None, None))
            if cat == 'graha_position':
                g = normalize_graha(subj)
                if g and g not in lords:
                    lords.append(g)
        if lords:
            return lords, None, 'ka_yojaka:dosha_constituent_grahas'

    # Unfired / requires_pass catalog-only dosha — correctly undated (dating a
    # catalog-only match would be fabrication).
    return [], None, None
