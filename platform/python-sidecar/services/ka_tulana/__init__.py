"""
services.ka_tulana — Cross-pattern prioritization service (L3 Kāla, QT-4).

Answers: "of my N windows, which matters most?" and "window A vs B — which
timing is more favorable, and why?"

Pure serve-time: no DB writes, no ctx.db_conn.commit().
Reads kala_convergence + kala_darshana (via caller-supplied data or DB conn).
"""
from .ranker import (
    KaTulanaService,
    RankedWindow,
    CompareVerdict,
    AttentionMap,
    KNOWN_DOMAINS,
    I11_WEIGHTS,
)

__all__ = [
    'KaTulanaService',
    'RankedWindow',
    'CompareVerdict',
    'AttentionMap',
    'KNOWN_DOMAINS',
    'I11_WEIGHTS',
]
