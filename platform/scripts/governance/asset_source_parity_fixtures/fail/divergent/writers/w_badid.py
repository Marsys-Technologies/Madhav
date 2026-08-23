"""FAIL fixture — a production id outside the six-prefix asset-id grammar (P-06)."""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)


@register('zz_bad')
class BadIdWriter:
    def run(self, ctx):
        return None
