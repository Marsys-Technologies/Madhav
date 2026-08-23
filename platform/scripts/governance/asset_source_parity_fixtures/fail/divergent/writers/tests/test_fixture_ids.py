"""FAIL-fixture control: a TEST-path registration. P-06 must NOT fire on it, because a
test-fixture id living under a test path is exactly where such an id belongs."""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)


@register('fixture.success')
class FixtureWriter:
    def run(self, ctx):
        return None
