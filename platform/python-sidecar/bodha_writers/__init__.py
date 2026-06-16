"""L2 Bodha writer package.

Contains the business logic for all eight bo_* asset writers plus the shared
helpers (_idempotency, formulas).  Thin orchestrator adapters live under
platform/python-sidecar/pipeline/orchestrator/writers/bo_*.py and import from
here exactly as the L1 ga_writers pattern does.

Design rules (inherited from L1, inherited by every future layer):
- DELETE-then-INSERT idempotency per chart × natural-key scope (_idempotency.py)
- All salience/linkage/resonance/convergence/centrality computations are
  pure, versioned, unit-tested functions (formulas.py)
- No ctx.db_conn commit / rollback / close inside any writer
- No asset_throughput writes
"""
