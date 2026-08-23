"""PASS fixture writer — the literal @register form.

The docstring deliberately mentions @register('bg_decoy_in_docstring'): a REGEX scanner
counts it (the M0-T1 defect); the AST parse this guard borrows from census.py does not.
"""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)


@register('bg_one')
class OneWriter:
    def run(self, ctx):
        return None
