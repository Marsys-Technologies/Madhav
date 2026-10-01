"""gochara_rules — Pravāha B5.1: data-driven rule-path catalogue and
evaluators P1–P6 (GOCHARA_DESIGN_SPECS_v1_4 §0–§5, §8).

Public surface:
  frames      — frame enum, inclusive house counting, sign_of
  registry    — rule_path registry rows, 27-class universe, P3 truth table,
                kāraka sets, P5 missing-input matrix, factor definitions
  predicates  — tri-state predicate evaluator (unknown ≠ false)
  records     — relationship_record, deterministic record_id, root_id,
                affliction predicate
  admission   — P2/P3/P4 admission evaluators
  score       — pinned within-path product / root reduction / cross-path max
  valence     — three-field valence (occurrence contested ≠ outcome mixed)
  permission  — permission_per_instant with the §4.0 pinned reference rows
  vedha       — vedha interval semantics (half-open; vipareeta carve-out)
  ashtakavarga— P5a..P5e qualifiers
  p6          — P6 Moon-channel operators, all testimony
  favourable_houses — P2 per-planet favourable house sets from janma-rāśi
                (Phaladīpikā XXVI.1–8, PG321–323), cited registry content
"""
from __future__ import annotations

from . import admission, ashtakavarga, dignity, favourable_houses  # noqa: F401
from . import frames, nature, p6  # noqa: F401
from . import permission, predicates  # noqa: F401
from . import records, registry, score, valence, vedha  # noqa: F401

__all__ = [
    "admission", "ashtakavarga", "dignity", "favourable_houses",
    "frames", "nature", "p6",
    "permission", "predicates", "records", "registry", "score", "valence",
    "vedha",
]
