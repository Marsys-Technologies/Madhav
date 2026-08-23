"""FAIL fixture — a production writer with no asset_registry row (P-02)."""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)


@register('bg_nowhere')
class NowhereWriter:
    def run(self, ctx):
        return None
