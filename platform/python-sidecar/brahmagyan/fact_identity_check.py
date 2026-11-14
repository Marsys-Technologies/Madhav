"""Compatibility alias for the Gaṇita-owned fact_identity_check implementation."""
import sys as _sys
from ga_writers import fact_identity_check as _implementation

_sys.modules[__name__] = _implementation
