"""Regression tests for the Nirmāṇa L0/L5 receipt-checker coupling fix.

NIRMANA_L0_L5_RECEIPT_COUPLING_FIX_ADDENDUM_v1_0.md (CCD-017): `build_pins()`
used to compute and validate every layer, INCLUDING L0's hardcoded
`L0_FROZEN_PINS` comparison, on every call -- even a `--layer L5` splice whose
only use for the result is L5's own record. That coupling is what blocked the
Jātaka Phase-A3 close's Nirmāṇa L5 re-pin (item 4): a real, unrelated L0 drift
(briefs/nirmana/JATAKA_PHASE_A3_L0_FROZEN_PINS_DRIFT_FINDING_v1_0.md) made
`build_pins()` refuse to run for L5 at all.

These tests use fully synthetic fixtures (fake asset ids, a fake
`L0_FROZEN_PINS`, fake git-commit stand-ins for `_pins_at_commit`/
`_inventory_at_commit`) so they exercise `build_pins()`/`splice_layer_pin()`
directly, hermetically, with no live database and no dependency on the real
repository's current L0/L5 state.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
MODULE_PATH = REPO / "platform/scripts/generate/nirmana_analysis_layer_pins.py"
SPEC = importlib.util.spec_from_file_location("nirmana_analysis_layer_pins_coupling", MODULE_PATH)
assert SPEC and SPEC.loader
pins_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pins_module)


L0_PREFIX = pins_module.LAYER_PREFIX["L0"]
L5_PREFIX = pins_module.LAYER_PREFIX["L5"]
FAKE_L0_ASSETS = ["bg_alpha", "bg_beta"]
FAKE_L5_ASSETS = ["mi_gamma", "mi_delta"]
FAKE_SNAPSHOT_COMMIT = "a" * 40
FAKE_CONVERGENCE_COMMIT = "b" * 40


def _digest(byte: str) -> str:
    return byte * 64


def _writer_digests(l0_values: dict[str, str], l5_values: dict[str, str]) -> dict[str, str]:
    return {**l0_values, **l5_values}


def _manifest_assets() -> list[dict[str, str]]:
    return [
        *({"asset_id": a, "layer": "L0"} for a in FAKE_L0_ASSETS),
        *({"asset_id": a, "layer": "L1"} for a in ["ga_one"]),
        *({"asset_id": a, "layer": "L2"} for a in ["bo_one"]),
        *({"asset_id": a, "layer": "L3"} for a in ["ka_one"]),
        *({"asset_id": a, "layer": "L4"} for a in ["ph_one"]),
        *({"asset_id": a, "layer": "L5"} for a in FAKE_L5_ASSETS),
    ]


def _base_writer_digests() -> dict[str, str]:
    return {
        "bg_alpha": _digest("1"),
        "bg_beta": _digest("2"),
        "ga_one": _digest("3"),
        "bo_one": _digest("4"),
        "ka_one": _digest("5"),
        "ph_one": _digest("6"),
        "mi_gamma": _digest("7"),
        "mi_delta": _digest("8"),
    }


def _snapshot_pins_for(writer_digests: dict[str, str]) -> dict[str, object]:
    """The definition-snapshot commit's own committed pins, one per layer,
    with no non-writer assets -- just enough for receipt_membership()."""
    layers = {}
    for layer, prefix in pins_module.LAYER_PREFIX.items():
        layers[layer] = {
            "asset_prefix": prefix,
            "non_writer_assets": [],
        }
    return {"layers": layers}


@pytest.fixture
def fake_l0_frozen(monkeypatch):
    """A hermetic L0_FROZEN_PINS matching the fixture's OWN L0 writer digests --
    tests that want to prove "L0 drift still fails" mutate the inventory passed
    to build_pins(), not this frozen record."""
    frozen = {
        "convergence_commit": "c" * 40,
        "writer_inventory_sha256": pins_module.layer_inventory_sha256(
            {"bg_alpha": _digest("1"), "bg_beta": _digest("2")}, L0_PREFIX
        ),
        "receipt_count": 2,
    }
    monkeypatch.setattr(pins_module, "L0_FROZEN_PINS", frozen)
    return frozen


@pytest.fixture
def fake_definition_snapshot(monkeypatch):
    """Wires _pins_at_commit/_inventory_at_commit for FAKE_SNAPSHOT_COMMIT so
    build_definition_bindings() (called inside build_pins()) can run without
    ever touching git or a live database."""
    base_writers = _base_writer_digests()
    snapshot_pins = _snapshot_pins_for(base_writers)

    def fake_pins_at_commit(commit: str) -> dict[str, object]:
        assert commit == FAKE_SNAPSHOT_COMMIT
        return snapshot_pins

    def fake_inventory_at_commit(commit: str) -> dict[str, str]:
        assert commit == FAKE_SNAPSHOT_COMMIT
        return base_writers

    monkeypatch.setattr(pins_module, "_pins_at_commit", fake_pins_at_commit)
    monkeypatch.setattr(pins_module, "_inventory_at_commit", fake_inventory_at_commit)
    return base_writers


def test_current_reviewed_l5_successor_passes(fake_l0_frozen, fake_definition_snapshot):
    """A legitimate, reviewed L5-only successor (only L5's writer digests moved)
    builds cleanly when scoped to L5 alone."""
    writer_digests = dict(fake_definition_snapshot)
    writer_digests["mi_gamma"] = _digest("9")  # the "reviewed" L5 source change

    result = pins_module.build_pins(
        writer_digests,
        _manifest_assets(),
        FAKE_CONVERGENCE_COMMIT,
        FAKE_SNAPSHOT_COMMIT,
        layers=["L5"],
    )

    assert set(result["layers"]) == {"L5"}
    assert result["layers"]["L5"]["convergence_commit"] == FAKE_CONVERGENCE_COMMIT
    assert result["layers"]["L5"]["writer_inventory_sha256"] == pins_module.layer_inventory_sha256(
        writer_digests, L5_PREFIX
    )


def test_changing_only_l5_does_not_request_an_l0_repin(fake_definition_snapshot, monkeypatch):
    """Scoping to L5 alone must never evaluate L0_FROZEN_PINS at all -- proven
    by setting it to a value that would fail closed if it were ever compared,
    and confirming build_pins(layers=["L5"]) still succeeds and returns no L0
    entry whatsoever (not in layers, not in history, not in definition_bindings)."""
    poison = {"convergence_commit": "z" * 40, "writer_inventory_sha256": "0" * 64, "receipt_count": 999}
    monkeypatch.setattr(pins_module, "L0_FROZEN_PINS", poison)

    writer_digests = dict(fake_definition_snapshot)
    writer_digests["mi_gamma"] = _digest("9")

    result = pins_module.build_pins(
        writer_digests,
        _manifest_assets(),
        FAKE_CONVERGENCE_COMMIT,
        FAKE_SNAPSHOT_COMMIT,
        layers=["L5"],
    )

    assert "L0" not in result["layers"]
    assert "L0" not in result["history"]
    assert "L0" not in result["definition_bindings"]


def test_mutating_a_frozen_l0_fingerprint_still_fails(fake_l0_frozen, fake_definition_snapshot):
    """When L0 IS in scope (whole-file regeneration), a real L0 writer-digest
    drift against the frozen record still fails closed."""
    writer_digests = dict(fake_definition_snapshot)
    writer_digests["bg_alpha"] = _digest("f")  # drifted away from fake_l0_frozen's basis

    with pytest.raises(SystemExit, match=r"L0 writer_inventory_sha256"):
        pins_module.build_pins(
            writer_digests,
            _manifest_assets(),
            FAKE_CONVERGENCE_COMMIT,
            FAKE_SNAPSHOT_COMMIT,
            layers=None,  # whole-file: L0 is included
        )


def test_mutating_l0_membership_still_fails(fake_l0_frozen, fake_definition_snapshot):
    """Removing an L0 asset from the frozen MANIFEST (a pure membership change
    -- the writer inventory itself is untouched, so writer_inventory_sha256
    still matches the frozen record) still fails closed via the frozen
    receipt_count comparison."""
    writer_digests = dict(fake_definition_snapshot)  # unchanged: bg_alpha/bg_beta digests intact
    manifest = [a for a in _manifest_assets() if a["asset_id"] != "bg_beta"]

    with pytest.raises(SystemExit, match=r"L0 receipt_count"):
        pins_module.build_pins(
            writer_digests,
            manifest,
            FAKE_CONVERGENCE_COMMIT,
            FAKE_SNAPSHOT_COMMIT,
            layers=None,
        )


def test_changing_l5_without_a_reviewed_successor_still_fails(fake_definition_snapshot):
    """L5 drifting relative to what the definition-snapshot commit's own
    membership certifies still fails closed -- the per-layer analogue of L0's
    frozen-pin check, driven by receipt_membership()/membership_sha256()
    instead of a hardcoded constant (L5 has no ratified-forever capsule set,
    so its authority is the definition snapshot, not a frozen literal)."""
    writer_digests = dict(fake_definition_snapshot)
    manifest = _manifest_assets() + [{"asset_id": "mi_unreviewed", "layer": "L5"}]
    writer_digests["mi_unreviewed"] = _digest("u")  # a membership change the snapshot never certified

    with pytest.raises(SystemExit, match=r"L5 database manifest differs"):
        pins_module.build_pins(
            writer_digests,
            manifest,
            FAKE_CONVERGENCE_COMMIT,
            FAKE_SNAPSHOT_COMMIT,
            layers=["L5"],
        )


def test_predecessor_histories_remain_immutable_across_a_splice(fake_l0_frozen, fake_definition_snapshot):
    """splice_layer_pin() carries every other layer's committed pin AND the
    entire history block through byte-for-byte -- a per-layer splice must
    never touch successor lineage (admit_successor()'s job, not this one's)."""
    committed = {
        "version": pins_module.PINS_VERSION,
        "layers": {
            "L0": {"asset_prefix": "bg_", "convergence_commit": "old-l0", "writer_inventory_sha256": "x", "receipt_count": 2, "non_writer_assets": []},
            "L5": {"asset_prefix": "mi_", "convergence_commit": "old-l5", "writer_inventory_sha256": "y", "receipt_count": 2, "non_writer_assets": []},
        },
        "history": {
            "L0": [{"generation_id": "l0:old:abc", "pin": {"asset_prefix": "bg_"}, "historical_snapshot_commit": "d" * 40, "superseded_by_generation_id": "l0:new:def", "writer_digests": {"bg_alpha": _digest("1")}}],
            "L5": [],
        },
        "definition_bindings": {
            "L0": {"schema_version": pins_module.DEFINITION_SCHEMA_VERSION, "snapshot_commit": "e" * 40, "membership_sha256": "old-binding"},
            "L5": {"schema_version": pins_module.DEFINITION_SCHEMA_VERSION, "snapshot_commit": "e" * 40, "membership_sha256": "old-binding"},
        },
    }
    writer_digests = dict(fake_definition_snapshot)
    writer_digests["mi_gamma"] = _digest("9")
    fresh = pins_module.build_pins(
        writer_digests,
        _manifest_assets(),
        FAKE_CONVERGENCE_COMMIT,
        FAKE_SNAPSHOT_COMMIT,
        layers=["L5"],
    )
    committed["definition_bindings"]["L5"]["membership_sha256"] = fresh[
        "definition_bindings"
    ]["L5"]["membership_sha256"]
    committed_before = copy.deepcopy(committed)

    updated = pins_module.splice_layer_pin(committed, "L5", fresh)

    assert updated["history"] == committed_before["history"]
    assert updated["layers"]["L0"] == committed_before["layers"]["L0"]
    assert updated["layers"]["L5"] != committed_before["layers"]["L5"]
    assert updated["layers"]["L5"]["writer_inventory_sha256"] == pins_module.layer_inventory_sha256(
        writer_digests, L5_PREFIX
    )
    # committed itself (the caller's dict) is never mutated in place
    assert committed == committed_before


def test_scoped_splice_preserves_the_accepted_definition_binding(fake_l0_frozen, fake_definition_snapshot):
    """A writer-only L5 re-pin may change the live inventory digest, but an
    unchanged membership must keep its already-accepted definition binding.

    Replacing only ``snapshot_commit`` is still a protected-baseline rewrite;
    this test catches exactly that regression while exercising the real splice.
    """
    writer_digests = dict(fake_definition_snapshot)
    writer_digests["mi_gamma"] = _digest("9")
    fresh = pins_module.build_pins(
        writer_digests,
        _manifest_assets(),
        FAKE_CONVERGENCE_COMMIT,
        FAKE_SNAPSHOT_COMMIT,
        layers=["L5"],
    )
    accepted_binding = copy.deepcopy(fresh["definition_bindings"]["L5"])
    accepted_binding["snapshot_commit"] = "d" * 40
    committed = {
        "version": pins_module.PINS_VERSION,
        "layers": {"L5": {"writer_inventory_sha256": "old"}},
        "history": {"L5": []},
        "definition_bindings": {"L5": accepted_binding},
    }

    updated = pins_module.splice_layer_pin(committed, "L5", fresh)

    assert updated["definition_bindings"]["L5"] == accepted_binding
    assert updated["layers"]["L5"]["writer_inventory_sha256"] != "old"


def test_scoped_splice_restores_the_protected_baseline_definition_binding(fake_l0_frozen, fake_definition_snapshot):
    """When a branch already rewrote the snapshot label, an explicitly supplied
    protected-baseline binding is the recovery authority; matching membership
    allows the generator to restore those accepted bytes without hand-editing
    the generated JSON.
    """
    writer_digests = dict(fake_definition_snapshot)
    writer_digests["mi_gamma"] = _digest("9")
    fresh = pins_module.build_pins(
        writer_digests,
        _manifest_assets(),
        FAKE_CONVERGENCE_COMMIT,
        FAKE_SNAPSHOT_COMMIT,
        layers=["L5"],
    )
    protected_binding = copy.deepcopy(fresh["definition_bindings"]["L5"])
    protected_binding["snapshot_commit"] = "d" * 40
    rewritten_binding = copy.deepcopy(fresh["definition_bindings"]["L5"])
    rewritten_binding["snapshot_commit"] = "c" * 40
    committed = {
        "version": pins_module.PINS_VERSION,
        "layers": {"L5": {"writer_inventory_sha256": "old"}},
        "history": {"L5": []},
        "definition_bindings": {"L5": rewritten_binding},
    }

    updated = pins_module.splice_layer_pin(
        committed,
        "L5",
        fresh,
        accepted_definition_binding=protected_binding,
    )

    assert updated["definition_bindings"]["L5"] == protected_binding


def test_direct_splice_recovery_restores_only_the_historical_predecessor(monkeypatch):
    """The repair path may rewind only the exact unversioned direct splice.

    Other layers, all histories, and accepted definition bindings must remain
    byte-identical so the subsequent ``admit_successor()`` call can append the
    governed L5 generation without laundering unrelated drift.
    """
    source_commit = "9" * 40
    baseline_l5 = {
        "asset_prefix": "mi_",
        "convergence_commit": "8" * 40,
        "non_writer_assets": ["lel_events"],
        "receipt_count": 3,
        "writer_inventory_sha256": "7" * 64,
    }
    definition = {
        "schema_version": pins_module.DEFINITION_SCHEMA_VERSION,
        "snapshot_commit": "6" * 40,
        "membership_sha256": "5" * 64,
    }
    baseline = {
        "version": pins_module.PINS_VERSION,
        "layers": {"L5": baseline_l5},
        "history": {"L5": []},
        "definition_bindings": {"L5": definition},
    }
    candidate_writers = {"mi_alpha": _digest("a")}
    direct_l5 = {
        **baseline_l5,
        "convergence_commit": source_commit,
        "writer_inventory_sha256": pins_module.layer_inventory_sha256(
            candidate_writers, L5_PREFIX
        ),
    }
    committed = {
        "version": pins_module.PINS_VERSION,
        "layers": {
            "L0": {"sentinel": "untouched"},
            "L5": direct_l5,
        },
        "history": {"L0": [{"sentinel": "untouched"}], "L5": []},
        "definition_bindings": {
            "L0": {"sentinel": "untouched"},
            "L5": definition,
        },
    }
    monkeypatch.setattr(pins_module, "_pins_at_commit", lambda commit: baseline)

    recovered = pins_module.recover_direct_splice_predecessor(
        committed,
        layer="L5",
        historical_snapshot_commit="4" * 40,
        candidate_writer_digests=candidate_writers,
        source_commit=source_commit,
    )

    assert recovered["layers"]["L5"] == baseline_l5
    assert recovered["layers"]["L0"] == committed["layers"]["L0"]
    assert recovered["history"] == committed["history"]
    assert recovered["definition_bindings"] == committed["definition_bindings"]
    assert committed["layers"]["L5"] == direct_l5


def test_direct_splice_recovery_rejects_history_drift(monkeypatch):
    """Recovery fails closed if the layer lineage is not baseline-identical."""
    source_commit = "9" * 40
    candidate_writers = {"mi_alpha": _digest("a")}
    baseline_pin = {
        "asset_prefix": "mi_",
        "convergence_commit": "8" * 40,
        "non_writer_assets": [],
        "receipt_count": 1,
        "writer_inventory_sha256": "7" * 64,
    }
    definition = {
        "schema_version": pins_module.DEFINITION_SCHEMA_VERSION,
        "snapshot_commit": "6" * 40,
        "membership_sha256": "5" * 64,
    }
    baseline = {
        "layers": {"L5": baseline_pin},
        "history": {"L5": []},
        "definition_bindings": {"L5": definition},
    }
    committed = {
        "layers": {
            "L5": {
                **baseline_pin,
                "convergence_commit": source_commit,
                "writer_inventory_sha256": pins_module.layer_inventory_sha256(
                    candidate_writers, L5_PREFIX
                ),
            }
        },
        "history": {"L5": [{"unexpected": "history"}]},
        "definition_bindings": {"L5": definition},
    }
    monkeypatch.setattr(pins_module, "_pins_at_commit", lambda commit: baseline)

    with pytest.raises(SystemExit, match="history differs from historical snapshot"):
        pins_module.recover_direct_splice_predecessor(
            committed,
            layer="L5",
            historical_snapshot_commit="4" * 40,
            candidate_writer_digests=candidate_writers,
            source_commit=source_commit,
        )


def test_whole_file_regeneration_still_computes_every_layer(fake_l0_frozen, fake_definition_snapshot):
    """The default (no `layers` argument) path is unchanged: every layer,
    L0 included, is derived and validated -- this fix only narrows what a
    SCOPED request touches, it does not narrow the whole-file path."""
    writer_digests = dict(fake_definition_snapshot)

    result = pins_module.build_pins(
        writer_digests,
        _manifest_assets(),
        FAKE_CONVERGENCE_COMMIT,
        FAKE_SNAPSHOT_COMMIT,
    )

    assert set(result["layers"]) == set(pins_module.LAYER_PREFIX)
    assert set(result["history"]) == set(pins_module.LAYER_PREFIX)
