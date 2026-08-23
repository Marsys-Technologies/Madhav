"""FAIL-fixture control writer: registered, in the registry, in the seed. Must NOT fire."""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)


@register('bg_ok')
class OkWriter:
    def run(self, ctx):
        return None
