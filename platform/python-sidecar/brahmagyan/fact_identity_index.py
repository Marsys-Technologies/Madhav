"""Compatibility alias for the Gaṇita-owned fact_identity_index implementation."""
import sys as _sys
from ga_writers import fact_identity_index as _implementation

_sys.modules[__name__] = _implementation
