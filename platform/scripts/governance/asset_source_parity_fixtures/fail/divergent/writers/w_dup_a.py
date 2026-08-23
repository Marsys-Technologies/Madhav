"""FAIL fixture — half of a duplicate registration (P-05); sibling is w_dup_b.py."""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)


@register('bg_dup')
class DupAWriter:
    def run(self, ctx):
        return None
