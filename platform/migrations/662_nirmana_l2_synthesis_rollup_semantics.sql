-- 662_nirmana_l2_synthesis_rollup_semantics.sql
--
-- NIRMĀṆA L2-W3 (D-SYNTHESIS). Ruling #1720 condition 3: the redefinition is
-- documented AT THE COLUMN, not only in a state file or an issue. "A reader in six
-- months meets the column, not this issue."
--
-- Documentation only — no data change, no schema change. The values are written by
-- bo_laksana_rerank; the paired writer change ships in the same PR (D-CND-06).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

-- ── system_convergence_count — REPURPOSED, and the header above it is stale ──
--
-- Ruling #1720 granted a per-signal redefinition after the definition plan §5 implied
-- was measured and rejected. The rejected one denormalised bodha_convergence through
-- domains_affected_array: it populated 50,044 of 50,104 rows with mean 5.93 / max 6 —
-- so nearly constant, and it measured a property of the signal's DOMAIN rather than of
-- the signal. A reader seeing "6" would reasonably conclude "six systems agree about
-- this signal", which is a claim nothing measured (CLAUDE.md §N.7 item 6).
--
-- IMPORTANT for the next reader: migration 325 files this column under the section
-- header "Digest hooks (for bo_samvada)" (325:127-129). That header is now STALE.
-- bo_samvada's digest is per (chart x ayanamsha), not per signal, and it already has
-- bodha_convergence.cross_tradition_count for that purpose. This column has been
-- repurposed to a per-signal quantity; a repurposed column under an unchanged header
-- is a trap, so the comment says so rather than only stating the new meaning.
COMMENT ON COLUMN bodha_msr_signals.system_convergence_count IS
  'Per-signal. The number of OTHER signals in the same (chart_id, ayanamsha_id) that share at '
  'least one constituent fact_subject with this signal — i.e. how much of the chart converges on '
  'this signal''s subject. NOT a count of jyotish systems (that is cross_system_consensus_count) '
  'and NOT a domain-level property. NULL means this signal has no resolvable constituent facts, '
  'so nothing was measured; 0 is a MEASURED zero meaning the signal shares no subject with any '
  'other and genuinely stands alone. Measured on the canonical chart: 7,012 positive (range '
  '1-997), 2,860 measured-zero, 131 NULL, per ayanamsha. Written by bo_laksana_rerank, which is '
  'the only point in the DAG where the complete signal set exists. NOTE: migration 325''s section '
  'header "Digest hooks (for bo_samvada)" above this column is STALE — the column was repurposed '
  'by NIRMANA L2-W3 under adjudication #1720.';

COMMENT ON COLUMN bodha_msr_signals.cross_system_consensus_count IS
  'Per-signal. The number of distinct jyotish traditions (signal_tradition) producing at least one '
  'signal about the same chart subject as this signal, within the same ayanamsha. Resolved through '
  'constituent_facts_array -> chart_facts.fact_subject, so it REFERENCES an L1 fact rather than '
  're-deriving one (CLAUDE.md §N.5). Subject-level and not fact-level: fact-level cross-tradition '
  'overlap was measured at 2 facts chart-wide, so any definition keyed on a shared fact_id is dead '
  'on arrival. Range 1-3 on the canonical chart, 2,485 rows at >= 2. NULL means no resolvable '
  'constituent facts. Written by bo_laksana_rerank.';

COMMENT ON COLUMN bodha_msr_signals.contradicts_signals_array IS
  'Per-signal denormalisation of bodha_contradictions (signal_a_id/signal_b_id, both directions). '
  'NULL — never an empty array — on signals that participate in no contradiction: bo_upaya probes '
  'this column and reads ''{}'' as a MEASURED "no contradictions found", which would enable its '
  'contradiction_factor term with no evidence behind it. That NULL-not-empty rule is the '
  'campaign''s standing convention for denormalised array columns (adjudication #1720). Written by '
  'bo_laksana_rerank, which runs after bo_karanajala populates the source table.';
