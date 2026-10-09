
SELECT
  (
    NOT EXISTS (
      SELECT 1
      FROM (SELECT DISTINCT chart_id FROM bodha_pratijna) c
      CROSS JOIN unnest(ARRAY[
        'krishnamurti','lahiri_chitrapaksha','raman',
        'surya_siddhanta_classical','true_chitra'
      ]) AS aya(ayanamsha_id)
      CROSS JOIN unnest(ARRAY[
        'achievement_recognition','bereavement','birth_anchor','business_launch',
        'career_advancement','career_change','career_entry','career_setback',
        'childbirth','chronic_onset','education_milestone','exam_outcome',
        'financial_deception','foreign_settlement','illness_acute','major_gain',
        'major_loss','marriage','parental_event','property_acquisition',
        'psychological_arc','relocation','romantic_start','separation',
        'spiritual_turn','surgery','travel_event'
      ]) AS ec(event_class_id)
      LEFT JOIN bodha_pratijna p
        ON p.chart_id = c.chart_id AND p.ayanamsha_id = aya.ayanamsha_id
       AND p.event_class_id = ec.event_class_id
      WHERE p.pratijna_id IS NULL
    )
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    GROUP BY chart_id, ayanamsha_id, event_class_id
    HAVING count(*) > 1
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE (status = 'no_evidence' AND grade IS NOT NULL)
       OR (status != 'no_evidence' AND grade IS NULL)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE grade IS NOT NULL AND (grade < 0 OR grade > 10)
  )
  AND NOT EXISTS (
    SELECT 1 FROM bodha_pratijna
    WHERE status NOT IN ('promised', 'denied', 'conditional', 'no_evidence')
  )
