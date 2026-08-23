"""FAIL fixture — the other half of the duplicate registration (P-05)."""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)


@register('bg_dup')
class DupBWriter:
    def run(self, ctx):
        return None
