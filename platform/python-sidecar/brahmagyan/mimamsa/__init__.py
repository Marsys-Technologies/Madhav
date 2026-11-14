"""
brahmagyan.mimamsa — Brahma L5 Mīmāṃsā (Calibration + Interpretation) layer.

Mīmāṃsā (Sanskrit: critical enquiry / exegesis) is the final epistemic layer.
It scores prediction outcomes against observed reality, maintaining a calibration
record per (technique, ayanamsha). The Learning Layer discipline rule:
- life_events (MI-5-1) and prediction_ledger (MI-5-2) are upstream inputs.
- NO LEAKAGE: life_events must NEVER feed into prediction generation —
  they feed ONLY into calibration after outcomes are observed.

Sub-modules:
    lel_intake         — mimamsa.lel_intake (MI-5-1)
                         One-time ingest of 57 LEL events into life_events +
                         event_chart_state_index tables.
                         Calibration corpus only — NO LEAKAGE into prediction generation.

    prediction_ledger  — mimamsa.prediction_ledger (MI-5-2)
                         Prospective prediction log (log_prediction + record_outcome).
                         The model logs prediction BEFORE the outcome is observed.

    outcome            — mimamsa.outcome (MI-5-3)
                         Outcome scoring: Brier score per prediction; calibration table.
                         Tool: record_outcome(prediction_id, outcome_observed)
                               → {brier_score, updated_calibration}

    multiplier         — mimamsa.multiplier (MI-5-4)
                         Bounded learning multiplier: modulates classical layer from outcomes.
                         learning_multiplier(technique, ayanamsha_id)
                             = 1.0 + 0.1 × (0.5 - mean_brier_score)
                         clamped to [0.8, 1.2]. Classical layer modulated NOT overwritten.

    Historical standalone commands — withdrawn from supported operation
  brahmagyan/bodha/bo_2-7.py and mimamsa/export_to_bigquery.py are no longer
  shipped. This does not assert that unknown manual callers never existed.
  The separate l5_bigquery_export compatibility API remains disabled.

  Offline source and original mocked-export fixtures are preserved at permanent
  main commit c5a0ffe2baee40014e3e8e80fbbde4ba3357d79d. Use git show with these
  exact paths to recover bytes into an isolated owner-approved noindex scratch:
    platform/python-sidecar/brahmagyan/bodha/bo_2-7.py
    platform/python-sidecar/brahmagyan/mimamsa/export_to_bigquery.py
    platform/python-sidecar/tests/test_mimamsa_export.py
  The original mocked tests provide the offline comparison/reference route;
  provider/embedding/vector equivalence is not inferred from other readers.
  Source recovery or rollback does not authorize a live export or embedding run.
  Restore the cohort's exact inverse to roll back current package/support edits.

l5_bigquery_export — mimamsa.bigquery_export (MI-5-5, legacy)
                         DISABLED: refusing stub. It used to build event rows incl.
                         free-text descriptions from the in-source corpus; it now
                         raises BigQueryExportDisabled on every entry point.

    answer_quality     — mimamsa.answer_quality (MI-5-6)
                         Golden Q&A eval: B.11 compliance detection, layer coverage,
                         grounding score, leakage guard.
                         10 golden Q&A pairs (2 per layer minimum).
                         All pairs: b11_compliance=TRUE, source_citation non-null (B.3).
"""
