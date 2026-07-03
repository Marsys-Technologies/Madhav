-- Migration 385: charts.chart_type column (BA-P3A Step 1)
-- Grounding: BA_MASTER C2 (chart_type absent; prashna/synastry prerequisite).
-- Default 'natal' so all existing rows are classified correctly.
-- Constraint: open enum via CHECK for extensibility (prashna, synastry added later).

ALTER TABLE charts
  ADD COLUMN IF NOT EXISTS chart_type TEXT NOT NULL DEFAULT 'natal'
    CHECK (chart_type IN ('natal', 'prashna', 'synastry', 'varshaphala'));

COMMENT ON COLUMN charts.chart_type IS
  'Chart category: natal (birth) | prashna (query) | synastry (relationship) | varshaphala (solar return). Default natal.';
