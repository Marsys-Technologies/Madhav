"""B5.3 — retrodiction harness for the Gochara evaluation protocol (v2.3).

Public surface:
  registry  — event-registry loader + validation (27-class universe, tiers, mask)
  extract   — generation-extract adapter (measured sha256, §4.5 adapter, §4.2 merge)
  metrics   — T-cover / T-time / T-rank / T-FP / T-honesty (protocol §5, §6, §8)
  controls  — frozen random-control reproduction check (protocol §7, seed 482012)
  oracles   — GOCHARA_TEST_ORACLES file validation + execution registry
  score     — full scoring pass → machine-readable result JSON
"""

from .registry import (
    ADVERSE_CLASSES,
    CLASSES_27,
    H0,
    H1,
    H_DAYS,
    CAP_DAYS,
    TIE_TOL,
    HeldEvent,
    Registry,
    load_registry,
)
from .extract import (
    InputRejected,
    MergedWindow,
    load_extract,
    merge_windows,
    measure_sha256,
)
from .metrics import (
    candidate_set,
    event_hit,
    score_generation,
)
from .controls import (
    CONTROLS_SEED,
    DRAWS_PER_EVENT,
    ControlsMismatch,
    draw_controls,
    verify_controls_file,
)
from .oracles import (
    OracleFileError,
    load_oracles,
    oracle_execution_registry,
)
from .score import run_scoring_pass

__all__ = [
    "ADVERSE_CLASSES",
    "CLASSES_27",
    "H0",
    "H1",
    "H_DAYS",
    "CAP_DAYS",
    "TIE_TOL",
    "HeldEvent",
    "Registry",
    "load_registry",
    "InputRejected",
    "MergedWindow",
    "load_extract",
    "merge_windows",
    "measure_sha256",
    "candidate_set",
    "event_hit",
    "score_generation",
    "CONTROLS_SEED",
    "DRAWS_PER_EVENT",
    "ControlsMismatch",
    "draw_controls",
    "verify_controls_file",
    "OracleFileError",
    "load_oracles",
    "oracle_execution_registry",
    "run_scoring_pass",
]
