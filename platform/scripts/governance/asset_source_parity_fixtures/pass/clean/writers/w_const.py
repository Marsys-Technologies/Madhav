"""PASS fixture writer — the @register(MODULE_CONSTANT) form.

This is the exact form M0-T8's first AST pass silently dropped, missing four writers of
which two were HEAVY. If this fixture ever stops resolving, the borrowed parser has
regressed and P-01/P-02 will say so out loud instead of quietly under-counting.
"""
from pipeline.orchestrator.registry import register   # noqa: F401  (fixture)

ASSET_ID = "bg_two"


@register(ASSET_ID)
class TwoWriter:
    def plan_substeps(self, ctx):
        return []

    def run_substep(self, ctx, step):
        return None
