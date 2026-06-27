-- Migration 346: Fix kala_* chart_id FK target
--
-- All six kala_* data tables were created with chart_id REFERENCES charts(chart_id)
-- instead of charts(id).  The orchestrator passes charts.id as the chart identifier,
-- so any non-native chart whose charts.id != charts.chart_id fails with FK violation
-- on first insert.  Drop the wrong constraints and re-add them pointing at charts(id).

ALTER TABLE kala_activation
  DROP CONSTRAINT kala_activation_chart_id_fkey,
  ADD CONSTRAINT kala_activation_chart_id_fkey
    FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE;

ALTER TABLE kala_bhavishya
  DROP CONSTRAINT kala_bhavishya_chart_id_fkey,
  ADD CONSTRAINT kala_bhavishya_chart_id_fkey
    FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE;

ALTER TABLE kala_convergence
  DROP CONSTRAINT kala_convergence_chart_id_fkey,
  ADD CONSTRAINT kala_convergence_chart_id_fkey
    FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE;

ALTER TABLE kala_darshana
  DROP CONSTRAINT kala_darshana_chart_id_fkey,
  ADD CONSTRAINT kala_darshana_chart_id_fkey
    FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE;

ALTER TABLE kala_jivana_parva
  DROP CONSTRAINT kala_jivana_parva_chart_id_fkey,
  ADD CONSTRAINT kala_jivana_parva_chart_id_fkey
    FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE;

ALTER TABLE kala_obstruction
  DROP CONSTRAINT kala_obstruction_chart_id_fkey,
  ADD CONSTRAINT kala_obstruction_chart_id_fkey
    FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE;
