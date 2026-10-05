-- TI-L2-21 re-check queries (reader-only SELECT; chart 482012f1-710e-4a25-994a-93821f5871aa)
-- Q1: which aspect-class categories carry an orb
select fact_category, count(*) facts,
       count(*) filter (where fact_value_jsonb ? 'orb_deg' or fact_key='orb_deg') with_orb_deg
  from chart_facts
 where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
   and (fact_category like 'aspect%' or fact_category in ('virupa_drishti','conjunction_per_varga','conjunction_within_orb',
        'lord_aspects_lord_per_varga','graha_effective_dignity_modified_by_aspects','bhava_bala_aspectual'))
 group by 1 order by 1;
-- Q2: L2 signals citing each category and their stored orb_tightness
with fam as (select fact_id::text fid, fact_category cat from chart_facts
              where chart_id='482012f1-710e-4a25-994a-93821f5871aa'
                and (fact_category like 'aspect%' or fact_category in ('virupa_drishti','conjunction_per_varga','conjunction_within_orb',
                     'lord_aspects_lord_per_varga','graha_effective_dignity_modified_by_aspects','bhava_bala_aspectual'))),
l as (select s.signal_id, s.orb_tightness, f.cat from bodha_msr_signals s join fam f on f.fid = any(s.constituent_facts_array)
       where s.chart_id='482012f1-710e-4a25-994a-93821f5871aa')
select cat, count(distinct signal_id) signals, min(orb_tightness) mn, max(orb_tightness) mx from l group by 1 order by 1;
-- Q3: orb_tightness over the whole chart, per producer
select producer_asset_id, count(*) n, count(*) filter (where orb_tightness is null) nulls,
       count(distinct orb_tightness) nd, min(orb_tightness), max(orb_tightness)
  from bodha_msr_signals where chart_id='482012f1-710e-4a25-994a-93821f5871aa' group by 1 order by 1;
-- Q4: the Tajika facts and the L2 signals that cite them
select f.fact_key, f.fact_subject, f.ayanamsha_id, f.fact_value_jsonb->>'orb_deg' orb_deg,
       f.fact_value_jsonb->>'orb_strength' orb_strength, s.signal_id, s.orb_tightness
  from bodha_msr_signals s join chart_facts f on f.fact_id::text = any(s.constituent_facts_array)
 where s.chart_id='482012f1-710e-4a25-994a-93821f5871aa' and f.fact_category='aspect_tajik' order by 1,2,3;
