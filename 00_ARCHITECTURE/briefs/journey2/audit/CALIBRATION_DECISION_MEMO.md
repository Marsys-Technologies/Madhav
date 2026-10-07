---
artifact: JOURNEY2_CONVERSATIONAL_CALIBRATION_MEMO
version: 1.1
status: DRAFT_REQUIRES_NATIVE_RULING
---

# Separate conversational calibration publication

Proposed ruling: adopt Option B of the standing PB-3 L-5 park. Create `mimamsa_conversational_calibration`, preserving `brahma_mimamsa_prediction_ledger` as the outcome authority and `mimamsa_calibration` as the existing analytical match table. This is COLLECT-ONLY: no model retrieval, prior adjustment, answer annotation, analytical scoring or asset count changes.

Current production ledger columns were inspected read-only on7October2026. The ledger has exact source-part/chart and original calculation stamps, outcome/confidence fields and `chart_context_stale_at`. The native still must approve this draft before schema/writer authoring.

Proposed additive table: `id uuid PRIMARY KEY DEFAULT gen_random_uuid()`, `chart_id uuid NOT NULL REFERENCES charts(id) ON DELETE CASCADE`, `prediction_ledger_row_id uuid NOT NULL REFERENCES brahma_mimamsa_prediction_ledger(id) ON DELETE CASCADE`, `source_citation uuid NOT NULL`, `domain text`, `confidence_point numeric`, `outcome text NOT NULL`, `outcome_value numeric`, `brier numeric`, `brier_excluded boolean NOT NULL`, `scoring_formula_version text NOT NULL`, `source_context jsonb NOT NULL`, `outcome_recorded_at timestamptz NOT NULL`, `scored_at timestamptz NOT NULL DEFAULT now()`. UNIQUE prediction_ledger_row_id; CHECK source_citation=prediction_ledger_row_id; bounded numeric values and legal outcome/null combinations. The proposed publication writer must enforce chart/source equality against the ledger under the same row lock; actual SQL tests must cover that invariant before acceptance. The existing ledger chart FK was refreshed live and references charts(id) ON DELETE CASCADE; use that verified target and preserve chart deletion semantics.

`source_context` copies exact original ledger stamps, message_part_id and source channel; it contains no consultation prose or outcome note. Formula version is fixed and explicit, with one current record per resolved claim. Retries verify/reuse the same outcome and formula; they do not overwrite historical scoring silently. A future formula change requires a separate version/backfill ruling.

Publish only confirmed, current-context eligible claims resolved through the owner-authorized recorder. Compute existing deterministic Brier from the human-confirmed confidence midpoint; `happened`=1, `did_not_happen`=0, `partial`=validated partial_value (default0.5), `unverifiable`=NULL and excluded. Missing confidence is NULL and excluded, never zero. Stale/context-superseded rows cannot produce a new learning sample; reporting excludes any publication whose source ledger later becomes stale. Outcome persistence and publication share one transaction/executor, with batch all-or-nothing rollback and no nested pool checkout. Return calibration_persisted=true only after the real write succeeds; expose failure accurately.

No historical backfill or invented samples. No modification of analytical mi_* writers, mimamsa_predictions, brahma_prospective_ledger or phala_anchors. Inaccessible to model retrieval capability catalog; do not broaden service-role grants. Verify existing DB ownership/no-leakage roles before choosing application access. If those roles cannot support the exact collect-only write without new permission, report that separate owner gate.

Acceptance: next-free migration reservation and static safety review; dedicated guarded disposable Postgres; missing/stale/wrong-chart/source mismatch, all four outcome classes, confidence-null, formula identity, retry uniqueness, single-connection pool, batch rollback and corrected-chart exclusion and actual chart/ledger deletion cascades; no-leakage source guard; truthful frontend publication state. Protected source review/CI, recoverable backup, exact migration and serving receipts, real owner acceptance using non-sensitive generated test claims. Existing factual predictions are not marked merely to obtain evidence.

## Changelog

- 1.0: concrete separate-sink proposal grounded in live ledger schema; native ruling pending, no source/DDL or learning publication performed.

- 1.1: draft review made both proposed deletion cascades explicit and requires real deletion regressions; no schema implementation or native adoption performed.
