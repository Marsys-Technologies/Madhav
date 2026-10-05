"""test_r78_criterion_registry.py — R78 (NIKASHA_CHANGE_REGISTER_v2_0.md, D4 ruling re-scope).

D4 (nikasha_test/DECISIONS_RECOMMENDATIONS_v2_0.md §D4): "obligation identity comes first; the id
is derived from it." Before this row, criteria were bare strings built inline as
`m["Gate.check"] = ...` assignments scattered through `measure()` (D4 finding #5: "no declarative
criterion list exists"), with nothing anywhere naming them as a closed, registered set. R78 adds
`CRITERION_REGISTRY` — every criterion carries a gate, check, applicability rule, detector binding
(the literal string `"NONE"` for a registered-but-unmeasured criterion — D4: "the honest form, not
a forbidden one" for a hand-only claim), and a revision — plus `registered_criterion()`, the one
lookup that resolves a criterion string against it.

Fails without the fix: `CRITERION_REGISTRY` and `registered_criterion` do not exist at all, and
every criterion string `measure()` actually assigns into `m[...]` is unregistered nowhere.
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

SRC = (HERE.parent / "asset_census.py").read_text(encoding="utf-8")

# Every criterion string measure() assigns into m[...] — extracted from the source rather than
# hardcoded here twice, so this test tracks the real function instead of a second, driftable list.
# (Excludes the literal example "Gate.check" that appears only inside this registry's own
# docstring, never as a real assignment.)
_EMITTED = sorted({c for c in re.findall(r'm\["([A-Za-z_.]+)"\]', SRC) if c != "Gate.check"})


def test_registry_exists_and_is_a_nonempty_dict():
    assert isinstance(ac.CRITERION_REGISTRY, dict)
    assert len(ac.CRITERION_REGISTRY) >= len(_EMITTED)


def test_every_criterion_measure_can_emit_is_registered():
    missing = [c for c in _EMITTED if c not in ac.CRITERION_REGISTRY]
    assert not missing, f"measure() assigns these criteria with no registry entry: {missing}"


def test_every_registry_entry_has_the_required_fields_and_a_consistent_criterion_string():
    required = {"gate", "check", "applicability", "detector", "revision"}
    for crit, entry in ac.CRITERION_REGISTRY.items():
        assert required <= set(entry), f"{crit} missing fields: {required - set(entry)}"
        assert isinstance(entry["revision"], int) and entry["revision"] >= 1, crit
        assert entry["detector"] == "NONE" or entry["detector"], crit
        # The derived-id format is <asset>-<Gate>.<check> — the criterion string itself must
        # already be exactly "Gate.check" (D4: the census's own pre-existing form).
        assert crit == f"{entry['gate']}.{entry['check']}", (
            f"{crit} inconsistent with its own gate/check fields: {entry['gate']}.{entry['check']}"
        )


def test_registered_criterion_returns_none_for_an_unregistered_string():
    assert ac.registered_criterion("Nonexistent.criterion") is None


def test_registered_criterion_returns_the_entry_for_a_registered_string():
    entry = ac.registered_criterion("Earn.build_record")
    assert entry is not None
    assert entry["gate"] == "Earn" and entry["check"] == "build_record"


def test_specific_hand_only_criteria_are_registered_with_detector_none_and_stay_distinct():
    """D4 review finding #2/#5: Completeness.depth.dasha_link and Earn.service_state (and Carr.D1/D2/D3,
    whose generic placeholder Carr.detector was retired at REGISTRY_REVISION 8 — see test_e6_i_*) are registered (so a hand row has somewhere to point) but with detector NONE (nothing in this
    script auto-measures them), and each is a DIFFERENT dict object from its generic placeholder —
    never merged by family alias."""
    for specific, generic in (
        ("Completeness.depth.dasha_link", "Complete.depth"),
        ("Earn.service_state", "Earn.build_record"),
    ):
        s, g = ac.registered_criterion(specific), ac.registered_criterion(generic)
        assert s is not None and g is not None, (specific, generic)
        # E5.7: Earn.service_state has a real detector (revision 2); Completeness.depth.dasha_link is still hand-only
        assert (s["detector"] == "NONE") == (specific == "Completeness.depth.dasha_link"), specific
        assert s is not g and s != g, f"{specific} must not be merged with {generic}"
