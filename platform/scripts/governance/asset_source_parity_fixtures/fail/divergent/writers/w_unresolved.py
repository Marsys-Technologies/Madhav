"""FAIL fixture — an @register argument the parser CANNOT resolve to a string.

This is P-01's whole reason to exist. A parser that silently skipped this line would
under-count the writer census by an unknown amount and every diff built on it would be
wrong by an unknown amount — which is worse than a loud failure, because it looks green.
"""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)

PREFIX = "bg"


@register(PREFIX + "_dynamic")
class DynamicWriter:
    def run(self, ctx):
        return None
