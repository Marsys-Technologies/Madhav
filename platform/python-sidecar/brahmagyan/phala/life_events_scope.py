"""Compatibility alias for the Phala-owned life event reader."""
import sys as _sys
from services.phala import life_events_scope as _implementation

_sys.modules[__name__] = _implementation
