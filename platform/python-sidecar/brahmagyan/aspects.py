"""Canonical parashari graha-drishti constants (BPHS Ch.26).

Single source of truth — import this; never declare a local graha→aspect dict.
The D-01 lint will enforce this going forward.
"""
# Rahu/Ketu cast the same special aspects as Jupiter per BPHS parashari mainstream.
NODE_PARASHARI_ASPECTS: dict[int, float] = {5: 1.0, 7: 1.0, 9: 1.0}
