"""One canonical digest for the overlay writers' upstream fingerprints (§12.9).

`ka_vedha_gochara` and `ka_moorti_nirnaya` each stamp a digest of the reference rows a build
consumed, so a later change to those tables is DETECTABLE. Both must hash the same way; one
implementation here means the two cannot drift apart.
"""
from __future__ import annotations

import hashlib
import json

FINGERPRINT_ALGORITHM = "sha256/canonical-json/v1"


def canonical_digest(obj) -> str:
    """sha256 over canonical JSON: sorted keys, no whitespace, non-ASCII kept, unknown types via str."""
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
