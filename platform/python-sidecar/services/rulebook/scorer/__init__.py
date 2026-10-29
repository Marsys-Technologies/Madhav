"""Rule Book scorer (yardstick v1.0 Parts 3/4/6 as amended by v1.1 Parts C, D, E).

Deterministic, seeded, numpy only. It reads per-unit-member state timelines (the engine
driver's output) and a list of episodes, and nothing else: no occurrence file, no chart
fact, no network. The scorer is frozen before any real occurrence is opened (v1.1 Part G);
after that an edit voids the result, so the module is small and every rule it applies is
named in ``config``.

Modules
-------
config    constants fixed by the yardstick, and the hash of the scorer source
model     Episode, MemberSpec, UnitSpec, ChartTimeline; unit structure from the manifest
core      curves, check (a) with min-p and Z25, checks (b)/(c), direction check
outcome   Holm, STRONG / MIDDLE / CHANCE-LEVEL, minimum detectable effect
footprint touch rates, the 0.60 gate, family testability
runner    the one-run ledger, the mechanical dry run
"""

from __future__ import annotations

SCORER_PACKAGE = "services.rulebook.scorer"
