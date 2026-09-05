from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "dispatch_nirmana_campaign_wave.py"
CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
REVISION = "t0-2026-08-25-4a78a5c4"


def _load_dispatch_module():
    if not SCRIPT_PATH.exists():
        return None
    spec = importlib.util.spec_from_file_location("dispatch_nirmana_campaign_wave", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _contract(*, sort_order: int, target_table: str) -> dict:
    return {
        "sort_order": sort_order,
        "scope": "global",
        "asset_kind": "data",
        "catalog_status": "CURRENT",
        "is_active": True,
        "has_writer": True,
        "target_table": target_table,
        "count_sql": f"SELECT count(*) FROM {target_table}",
        "integrity_check_sql": f"SELECT count(*) > 0 FROM {target_table}",
        "health_probe": None,
        "natural_key_partition": None,
        "superseded_by": None,
        "data_disposition": "RETAINED_AS_CAPITAL",
        "dead_flag": False,
    }


def _definition_manifest() -> dict:
    return {
        "chart_id": CHART_ID,
        "assets": [
            {
                "asset_id": "bg_reference",
                "layer": "L0",
                "wave_index": 0,
                "execution_obligation": "build",
                "depends_on": [],
                "registry_contract": _contract(sort_order=20, target_table="bg_reference"),
                "registry_fingerprint_sha256": "1" * 64,
            },
            {
                "asset_id": "bg_formula_constants",
                "layer": "L0",
                "wave_index": 0,
                "execution_obligation": "build",
                "depends_on": [],
                "registry_contract": _contract(sort_order=10, target_table="bg_formula_constants"),
                "registry_fingerprint_sha256": "2" * 64,
            },
            {
                "asset_id": "bg_panchanga",
                "layer": "L0",
                "wave_index": 0,
                "execution_obligation": "probe",
                "depends_on": [],
                "registry_contract": {
                    **_contract(sort_order=30, target_table="bg_panchanga"),
                    "asset_kind": "service",
                },
                "registry_fingerprint_sha256": "3" * 64,
            },
            {
                "asset_id": "bg_text_index",
                "layer": "L0",
                "wave_index": 1,
                "execution_obligation": "build",
                "depends_on": ["bg_reference"],
                "registry_contract": _contract(sort_order=40, target_table="bg_text_index"),
                "registry_fingerprint_sha256": "4" * 64,
            },
        ],
    }


def _candidate(asset: dict, *, has_cowriters: bool = False) -> dict:
    contract = asset["registry_contract"]
    return {
        "asset_id": asset["asset_id"],
        "layer": "brahmagyan",
        "depends_on": list(asset["depends_on"]),
        **contract,
        "has_cowriters": has_cowriters,
    }


def _digest(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _registry_fingerprint(candidate: dict) -> str:
    return _digest({
        "asset_id": candidate["asset_id"],
        "layer": "L0",
        "depends_on": candidate["depends_on"],
        "registry_contract": {
            field: candidate[field]
            for field in (
                "sort_order", "scope", "asset_kind", "catalog_status",
                "is_active", "has_writer", "target_table", "count_sql",
                "integrity_check_sql", "health_probe", "natural_key_partition",
                "superseded_by", "data_disposition", "dead_flag",
            )
        },
    })


def _evidence_row(
    *,
    event_id: int,
    asset_id: str,
    event_type: str,
    registry_fingerprint_sha256: str,
    analysis_digest: str,
    verdict: str = "examined_and_already_efficient",
    source_ref: str = "git:" + "a" * 40,
) -> dict:
    payload = {
        "registry_fingerprint_sha256": registry_fingerprint_sha256,
        "analysis_digest": analysis_digest,
    }
    if event_type == "optimization_verdict_accepted":
        payload.update({
            "verdict": verdict,
            "basis": {
                "measurement": {
                    "status": "measured",
                    "sample_count": 10,
                    "p50_ms": 2.0,
                    "p90_ms": 3.0,
                    "hotspot": None,
                },
                "evidence_refs": ["artifact:analysis"],
            },
            "proposal": {
                "action": "no_change",
                "summary": "Measured and already efficient.",
                "output_contract": "digest_identical",
            },
        })
    return {
        "event_id": event_id,
        "entity_id": asset_id,
        "event_type": event_type,
        "evidence_payload": payload,
        "source_kind": "git_commit",
        "source_ref": source_ref,
    }


def test_builds_exact_build_obligation_wave_in_frozen_manifest_order() -> None:
    module = _load_dispatch_module()
    assert module is not None, "the governed campaign-wave dispatcher is missing"
    definition = _definition_manifest()
    selected = [definition["assets"][0], definition["assets"][1]]

    manifest, digest, asset_ids = module.build_campaign_wave_manifest(
        chart_id=CHART_ID,
        definition_revision=REVISION,
        definition_manifest=definition,
        definition_manifest_digest=_digest(definition),
        layer="L0",
        wave_index=0,
        candidates=[_candidate(asset) for asset in reversed(selected)],
        writer_digests={"bg_reference": "a" * 64, "bg_formula_constants": "b" * 64},
    )

    assert asset_ids == ["bg_reference", "bg_formula_constants"]
    assert manifest == {
        "version": "nirmana-run-manifest/v1",
        "chart_id": CHART_ID,
        "scope": "asset_set",
        "scope_target": "bg_reference,bg_formula_constants",
        "action": "rebuild",
        "waves": [["bg_reference", "bg_formula_constants"]],
        "assets": [
            {
                "asset_id": "bg_reference",
                "scope": "global",
                "depends_on": [],
                "natural_key_partition": None,
                "has_cowriters": False,
                "expected_code_digest": "a" * 64,
                "registry_contract": _contract(
                    sort_order=20,
                    target_table="bg_reference",
                ),
                "registry_fingerprint_sha256": _registry_fingerprint(
                    _candidate(selected[0]),
                ),
            },
            {
                "asset_id": "bg_formula_constants",
                "scope": "global",
                "depends_on": [],
                "natural_key_partition": None,
                "has_cowriters": False,
                "expected_code_digest": "b" * 64,
                "registry_contract": _contract(
                    sort_order=10,
                    target_table="bg_formula_constants",
                ),
                "registry_fingerprint_sha256": _registry_fingerprint(
                    _candidate(selected[1]),
                ),
            },
        ],
    }
    assert digest == _digest(manifest)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("wrong_chart", "approved chart"),
        ("missing_revision", "definition revision"),
        ("bad_definition_digest", "definition manifest digest"),
        ("dependency_drift", "depends_on"),
        ("layer_drift", "layer"),
        ("unbuildable_live_contract", "not buildable"),
        ("missing_candidate", "live registry row"),
        ("missing_writer_digest", "writer digest"),
    ],
)
def test_refuses_identity_definition_registry_or_code_drift(mutation: str, message: str) -> None:
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()
    selected = [definition["assets"][0], definition["assets"][1]]
    kwargs = {
        "chart_id": CHART_ID,
        "definition_revision": REVISION,
        "definition_manifest": definition,
        "definition_manifest_digest": _digest(definition),
        "layer": "L0",
        "wave_index": 0,
        "candidates": [_candidate(asset) for asset in selected],
        "writer_digests": {"bg_reference": "a" * 64, "bg_formula_constants": "b" * 64},
    }
    if mutation == "wrong_chart":
        kwargs["chart_id"] = "11111111-1111-4111-8111-111111111111"
    elif mutation == "missing_revision":
        kwargs["definition_revision"] = ""
    elif mutation == "bad_definition_digest":
        kwargs["definition_manifest_digest"] = "0" * 64
    elif mutation == "dependency_drift":
        kwargs["candidates"][0]["depends_on"] = ["bg_formula_constants"]
    elif mutation == "layer_drift":
        kwargs["candidates"][0]["layer"] = "ganita"
    elif mutation == "unbuildable_live_contract":
        kwargs["candidates"][0]["is_active"] = False
    elif mutation == "missing_candidate":
        kwargs["candidates"] = kwargs["candidates"][:-1]
    elif mutation == "missing_writer_digest":
        del kwargs["writer_digests"]["bg_reference"]

    with pytest.raises(ValueError, match=message):
        module.build_campaign_wave_manifest(**kwargs)


def test_uses_reviewed_live_registry_contract_after_t0_without_changing_frozen_identity() -> None:
    """Catches restoring operational fields from frozen T0 instead of the reviewed live row."""
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()
    selected = [definition["assets"][0], definition["assets"][1]]
    candidates = [_candidate(asset) for asset in selected]
    candidates[0]["count_sql"] = "SELECT count(*) FROM bg_reference WHERE enabled"
    candidates[0]["integrity_check_sql"] = "SELECT bool_and(enabled) FROM bg_reference"

    manifest, _, _ = module.build_campaign_wave_manifest(
        chart_id=CHART_ID,
        definition_revision=REVISION,
        definition_manifest=definition,
        definition_manifest_digest=_digest(definition),
        layer="L0",
        wave_index=0,
        candidates=candidates,
        writer_digests={"bg_reference": "a" * 64, "bg_formula_constants": "b" * 64},
    )

    first = manifest["assets"][0]
    assert first["depends_on"] == []
    assert first["registry_contract"]["count_sql"] == candidates[0]["count_sql"]
    assert first["registry_contract"]["integrity_check_sql"] == candidates[0]["integrity_check_sql"]
    assert first["registry_fingerprint_sha256"] == _registry_fingerprint(candidates[0])


def test_accepts_only_one_exact_current_analysis_and_bound_verdict_per_asset() -> None:
    """Catches accepting any event names without binding them to the current contract pair."""
    module = _load_dispatch_module()
    assert module is not None
    current_fingerprint = "1" * 64
    analysis_digest = "2" * 64

    bindings = module.validate_wave_evidence_bindings(
        asset_ids=["bg_reference"],
        live_registry_fingerprints={"bg_reference": current_fingerprint},
        evidence_rows=[
            _evidence_row(
                event_id=1,
                asset_id="bg_reference",
                event_type="asset_analysis_accepted",
                registry_fingerprint_sha256=current_fingerprint,
                analysis_digest=analysis_digest,
            ),
            _evidence_row(
                event_id=2,
                asset_id="bg_reference",
                event_type="optimization_verdict_accepted",
                registry_fingerprint_sha256=current_fingerprint,
                analysis_digest=analysis_digest,
            ),
        ],
    )

    assert bindings == {
        "bg_reference": {
            "registry_fingerprint_sha256": current_fingerprint,
            "analysis_digest": analysis_digest,
        }
    }


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        (
            [
                _evidence_row(
                    event_id=1,
                    asset_id="bg_reference",
                    event_type="asset_analysis_accepted",
                    registry_fingerprint_sha256="3" * 64,
                    analysis_digest="2" * 64,
                ),
                _evidence_row(
                    event_id=2,
                    asset_id="bg_reference",
                    event_type="optimization_verdict_accepted",
                    registry_fingerprint_sha256="3" * 64,
                    analysis_digest="2" * 64,
                ),
            ],
            "current live registry contract",
        ),
        (
            [
                _evidence_row(
                    event_id=1,
                    asset_id="bg_reference",
                    event_type="asset_analysis_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                ),
                _evidence_row(
                    event_id=2,
                    asset_id="bg_reference",
                    event_type="optimization_verdict_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="4" * 64,
                ),
            ],
            "same accepted analysis",
        ),
        (
            [
                _evidence_row(
                    event_id=1,
                    asset_id="bg_reference",
                    event_type="asset_analysis_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                ),
                _evidence_row(
                    event_id=2,
                    asset_id="bg_reference",
                    event_type="asset_analysis_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                ),
                _evidence_row(
                    event_id=3,
                    asset_id="bg_reference",
                    event_type="optimization_verdict_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                ),
            ],
            "ambiguous asset analysis",
        ),
        (
            [
                _evidence_row(
                    event_id=1,
                    asset_id="bg_reference",
                    event_type="asset_analysis_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                ),
                _evidence_row(
                    event_id=2,
                    asset_id="bg_reference",
                    event_type="optimization_verdict_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                ),
                _evidence_row(
                    event_id=3,
                    asset_id="bg_reference",
                    event_type="optimization_verdict_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                ),
            ],
            "ambiguous optimization verdict",
        ),
        (
            [
                _evidence_row(
                    event_id=1,
                    asset_id="bg_reference",
                    event_type="asset_analysis_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                ),
                _evidence_row(
                    event_id=2,
                    asset_id="bg_reference",
                    event_type="optimization_verdict_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                    verdict="non_build_disposition",
                ),
            ],
            "does not authorize a build",
        ),
    ],
)
def test_rejects_stale_unbound_or_multiple_wave_evidence(rows: list[dict], message: str) -> None:
    module = _load_dispatch_module()
    assert module is not None

    with pytest.raises(RuntimeError, match=message):
        module.validate_wave_evidence_bindings(
            asset_ids=["bg_reference"],
            live_registry_fingerprints={"bg_reference": "1" * 64},
            evidence_rows=rows,
        )


def test_l0_dispatch_receipt_binding_accepts_current_deployment_and_excludes_history(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Receipt grounding M and deployed source P are distinct, append-only pins."""
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()
    selected = [definition["assets"][0], definition["assets"][1]]
    candidates = {_candidate(asset)["asset_id"]: _candidate(asset) for asset in selected}
    writer_digests = {"bg_reference": "a" * 64, "bg_formula_constants": "b" * 64}
    convergence_sha = "c" * 40
    deployed_sha = "d" * 40
    receipts_path = tmp_path / "nirmana-l0-analysis-receipts.ts"
    receipts_path.write_text(
        "\n".join(
            [
                f"export const NIRMANA_L0_CONVERGENCE_COMMIT = '{convergence_sha}' as const",
                "export const NIRMANA_L0_WRITER_INVENTORY_SHA256 = "
                f"'{_digest(writer_digests)}' as const",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "L0_ANALYSIS_RECEIPTS_PATH", receipts_path)

    receipt_digests, receipt_convergence_sha = module._current_l0_analysis_receipt_digests(
        selected_assets=selected,
        candidates_by_id=candidates,
        writer_digests=writer_digests,
    )
    assert receipt_convergence_sha == convergence_sha
    assert receipt_convergence_sha != deployed_sha
    module.validate_wave_evidence_bindings(
        asset_ids=["bg_reference"],
        live_registry_fingerprints={"bg_reference": _registry_fingerprint(candidates["bg_reference"])},
        canonical_analysis_digests={"bg_reference": receipt_digests["bg_reference"]},
        reviewed_deployment_sha=deployed_sha,
        evidence_rows=[
            # Valid historical receipt pair from M: retain it, but do not
            # let it make the current P-bound pair ambiguous.
            _evidence_row(
                event_id=1,
                asset_id="bg_reference",
                event_type="asset_analysis_accepted",
                registry_fingerprint_sha256=_registry_fingerprint(candidates["bg_reference"]),
                analysis_digest="e" * 64,
                source_ref=f"git:{convergence_sha}",
            ),
            _evidence_row(
                event_id=2,
                asset_id="bg_reference",
                event_type="optimization_verdict_accepted",
                registry_fingerprint_sha256=_registry_fingerprint(candidates["bg_reference"]),
                analysis_digest="e" * 64,
                source_ref=f"git:{convergence_sha}",
            ),
            _evidence_row(
                event_id=3,
                asset_id="bg_reference",
                event_type="asset_analysis_accepted",
                registry_fingerprint_sha256=_registry_fingerprint(candidates["bg_reference"]),
                analysis_digest=receipt_digests["bg_reference"],
                source_ref=f"git:{deployed_sha}",
            ),
            _evidence_row(
                event_id=4,
                asset_id="bg_reference",
                event_type="optimization_verdict_accepted",
                registry_fingerprint_sha256=_registry_fingerprint(candidates["bg_reference"]),
                analysis_digest=receipt_digests["bg_reference"],
                source_ref=f"git:{deployed_sha}",
            ),
        ],
    )

    drifted_digests = {**writer_digests, "bg_reference": "d" * 64}
    with pytest.raises(RuntimeError, match="writer inventory.*convergence"):
        module._current_l0_analysis_receipt_digests(
            selected_assets=selected,
            candidates_by_id=candidates,
            writer_digests=drifted_digests,
        )


def test_l0_dispatch_receipt_binding_rejects_stale_convergence_source() -> None:
    module = _load_dispatch_module()
    assert module is not None
    convergence_sha = "c" * 40
    deployed_sha = "d" * 40
    with pytest.raises(RuntimeError, match="current live registry contract"):
        module.validate_wave_evidence_bindings(
            asset_ids=["bg_reference"],
            live_registry_fingerprints={"bg_reference": "1" * 64},
            canonical_analysis_digests={"bg_reference": "2" * 64},
            reviewed_deployment_sha=deployed_sha,
            evidence_rows=[
                _evidence_row(
                    event_id=1,
                    asset_id="bg_reference",
                    event_type="asset_analysis_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                    source_ref=f"git:{convergence_sha}",
                ),
                _evidence_row(
                    event_id=2,
                    asset_id="bg_reference",
                    event_type="optimization_verdict_accepted",
                    registry_fingerprint_sha256="1" * 64,
                    analysis_digest="2" * 64,
                    source_ref=f"git:{convergence_sha}",
                ),
            ],
        )


def test_refuses_empty_or_nonbuild_only_wave() -> None:
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()

    with pytest.raises(ValueError, match="no build obligations"):
        module.build_campaign_wave_manifest(
            chart_id=CHART_ID,
            definition_revision=REVISION,
            definition_manifest=definition,
            definition_manifest_digest=_digest(definition),
            layer="L0",
            wave_index=9,
            candidates=[],
            writer_digests={},
        )


def test_selects_only_the_requested_asset_subset_of_the_wave() -> None:
    """Per-asset dispatch control: narrows the wave without reordering it."""
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()

    selected = module._select_frozen_build_assets(
        chart_id=CHART_ID,
        definition_revision=REVISION,
        definition_manifest=definition,
        definition_manifest_digest=_digest(definition),
        layer="L0",
        wave_index=0,
        asset_ids=frozenset({"bg_formula_constants"}),
    )

    assert [asset["asset_id"] for asset in selected] == ["bg_formula_constants"]


def test_refuses_a_subset_naming_an_asset_outside_the_wave_build_obligation() -> None:
    """A typo'd or out-of-wave asset_id must fail loudly, never silently drop."""
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()

    with pytest.raises(ValueError, match="no build obligation for: bg_reference_typo"):
        module._select_frozen_build_assets(
            chart_id=CHART_ID,
            definition_revision=REVISION,
            definition_manifest=definition,
            definition_manifest_digest=_digest(definition),
            layer="L0",
            wave_index=0,
            asset_ids=frozenset({"bg_formula_constants", "bg_reference_typo"}),
        )


def test_refuses_a_subset_naming_a_probe_only_or_other_wave_asset() -> None:
    """bg_panchanga is probe-only and bg_text_index is wave 1 -- neither is a build
    obligation of L0 wave 0, so requesting either must be refused the same as a typo."""
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()

    with pytest.raises(ValueError, match="no build obligation for: bg_text_index"):
        module._select_frozen_build_assets(
            chart_id=CHART_ID,
            definition_revision=REVISION,
            definition_manifest=definition,
            definition_manifest_digest=_digest(definition),
            layer="L0",
            wave_index=0,
            asset_ids=frozenset({"bg_text_index"}),
        )


def test_build_campaign_wave_manifest_narrows_to_the_requested_asset_subset() -> None:
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()
    selected = [definition["assets"][1]]  # bg_formula_constants only

    manifest, digest, asset_ids = module.build_campaign_wave_manifest(
        chart_id=CHART_ID,
        definition_revision=REVISION,
        definition_manifest=definition,
        definition_manifest_digest=_digest(definition),
        layer="L0",
        wave_index=0,
        candidates=[_candidate(asset) for asset in selected],
        writer_digests={"bg_formula_constants": "b" * 64},
        requested_asset_ids=frozenset({"bg_formula_constants"}),
    )

    assert asset_ids == ["bg_formula_constants"]
    assert manifest["scope_target"] == "bg_formula_constants"
    assert manifest["waves"] == [["bg_formula_constants"]]
    assert digest == _digest(manifest)


def test_triggered_by_is_wave_scoped_without_a_subset_and_asset_scoped_with_one() -> None:
    module = _load_dispatch_module()
    assert module is not None

    wave_scoped = module._triggered_by(REVISION, "L0", 0)
    subset_scoped = module._triggered_by(
        REVISION, "L0", 0, asset_ids=frozenset({"bg_formula_constants"})
    )
    reordered_subset_scoped = module._triggered_by(
        REVISION, "L0", 0, asset_ids=frozenset({"bg_formula_constants"})
    )

    assert wave_scoped == f"{module.CAMPAIGN_ID}:{REVISION}:L0:wave-0"
    assert subset_scoped == f"{wave_scoped}:assets-bg_formula_constants"
    # A scoped run must never collide with (or be confused for) the full-wave slot.
    assert subset_scoped != wave_scoped
    # Deterministic regardless of set iteration/construction order.
    assert subset_scoped == reordered_subset_scoped
    two_asset_scoped = module._triggered_by(
        REVISION, "L0", 0, asset_ids=frozenset({"bg_reference", "bg_formula_constants"})
    )
    assert two_asset_scoped == f"{wave_scoped}:assets-bg_formula_constants,bg_reference"


def test_derives_egate_ancestor_closure_not_strict_layer_wave_sequencing() -> None:
    """Charter C2 condition 1: the gate is the transitive depends_on closure.

    This test replaces test_derives_strict_prior_layer_and_wave_freeze_prerequisites,
    which asserted the pre-v2.1 rule -- every asset of every lower-ranked layer plus
    every earlier wave of the same layer, dependency edges never consulted. That rule
    was correct for the sequential topology it was written for and is wrong for the
    ratified one: under it, no layer session could dispatch anything at all.

    The fixture shows the difference exactly. `bg_text_index` is wave 1 and depends on
    `bg_reference` alone. The old rule demanded all three wave-0 assets frozen; the
    E-gate demands the one it actually depends on.
    """
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()

    # No dependencies -> nothing gates it, regardless of layer or wave.
    assert module.campaign_prerequisite_asset_ids(
        definition_manifest=definition,
        layer="L0",
        wave_index=0,
        dispatch_asset_ids=["bg_reference"],
    ) == []

    # The behavioural difference, stated as an assertion: one real ancestor, not the
    # two unrelated wave-0 assets the strict rule would also have demanded.
    assert module.campaign_prerequisite_asset_ids(
        definition_manifest=definition,
        layer="L0",
        wave_index=1,
        dispatch_asset_ids=["bg_text_index"],
    ) == ["bg_reference"]
    assert "bg_formula_constants" not in module.campaign_prerequisite_asset_ids(
        definition_manifest=definition,
        layer="L0",
        wave_index=1,
        dispatch_asset_ids=["bg_text_index"],
    )


def test_egate_closure_is_transitive_excludes_self_and_dedupes() -> None:
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()
    # a -> b -> c, plus a second dispatched asset sharing ancestor c.
    definition["assets"] = [
        {**definition["assets"][0], "asset_id": "x_c", "depends_on": []},
        {**definition["assets"][0], "asset_id": "x_b", "depends_on": ["x_c"]},
        {**definition["assets"][0], "asset_id": "x_a", "depends_on": ["x_b"]},
        {**definition["assets"][0], "asset_id": "x_d", "depends_on": ["x_c"]},
    ]

    # Transitive: dispatching x_a requires x_b AND x_c, not just x_b.
    assert module.campaign_prerequisite_asset_ids(
        definition_manifest=definition, layer="L0", wave_index=0,
        dispatch_asset_ids=["x_a"],
    ) == ["x_b", "x_c"]

    # Shared ancestor appears once; a co-dispatched asset never gates its sibling.
    assert module.campaign_prerequisite_asset_ids(
        definition_manifest=definition, layer="L0", wave_index=0,
        dispatch_asset_ids=["x_a", "x_d"],
    ) == ["x_b", "x_c"]

    # An asset is never its own prerequisite.
    assert "x_b" not in module.campaign_prerequisite_asset_ids(
        definition_manifest=definition, layer="L0", wave_index=0,
        dispatch_asset_ids=["x_b", "x_a"],
    )


def test_egate_closure_fails_closed_on_bad_manifest_data() -> None:
    """Fail-closed on data, never hang and never silently narrow the gate."""
    module = _load_dispatch_module()
    assert module is not None

    cyclic = _definition_manifest()
    cyclic["assets"] = [
        {**cyclic["assets"][0], "asset_id": "y_a", "depends_on": ["y_b"]},
        {**cyclic["assets"][0], "asset_id": "y_b", "depends_on": ["y_a"]},
    ]
    # Terminates rather than looping; the cycle partner still gates.
    assert module.campaign_prerequisite_asset_ids(
        definition_manifest=cyclic, layer="L0", wave_index=0,
        dispatch_asset_ids=["y_a"],
    ) == ["y_b"]

    dangling = _definition_manifest()
    dangling["assets"] = [
        {**dangling["assets"][0], "asset_id": "z_a", "depends_on": ["z_missing"]},
    ]
    with pytest.raises(ValueError, match="dangling depends_on"):
        module.campaign_prerequisite_asset_ids(
            definition_manifest=dangling, layer="L0", wave_index=0,
            dispatch_asset_ids=["z_a"],
        )

    unknown = _definition_manifest()
    with pytest.raises(ValueError, match="not in the frozen definition"):
        module.campaign_prerequisite_asset_ids(
            definition_manifest=unknown, layer="L0", wave_index=0,
            dispatch_asset_ids=["bg_not_a_real_asset"],
        )


def test_concurrent_campaign_run_cap_matches_the_ratified_charter_budget() -> None:
    """Charter C5 publishes three slots; the tool must permit three, not one.

    The guard was previously an unconditional `if active:` -- any run in flight
    anywhere refused the dispatch -- which made slots 2 and 3 of the published ledger
    unreachable, so the second session to claim a slot would fail after posting a
    valid claim. This pins the cap to the ratified number so a future edit that
    silently reverts it to 1 (or raises it without re-measuring connection headroom)
    fails here.
    """
    module = _load_dispatch_module()
    assert module is not None
    assert module.MAX_CONCURRENT_CAMPAIGN_RUNS == 3


def test_binds_snapshot_reference_into_previewed_runner_manifest() -> None:
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()
    selected = [definition["assets"][0], definition["assets"][1]]

    manifest, digest, _ = module.build_campaign_wave_manifest(
        chart_id=CHART_ID,
        definition_revision=REVISION,
        definition_manifest=definition,
        definition_manifest_digest=_digest(definition),
        layer="L0",
        wave_index=0,
        candidates=[_candidate(asset) for asset in selected],
        writer_digests={"bg_reference": "a" * 64, "bg_formula_constants": "b" * 64},
        snapshot_ref="cloudsql-backup:nirmana-l0-wave0-20260825",
    )

    assert manifest["campaign_control"] == {
        "campaign_id": "nirmana-elevation",
        "definition_revision": REVISION,
        "layer": "L0",
        "wave_index": 0,
        "snapshot_ref": "cloudsql-backup:nirmana-l0-wave0-20260825",
    }
    assert digest == _digest(manifest)


def test_accepts_an_exact_future_frozen_revision_without_a_code_release() -> None:
    module = _load_dispatch_module()
    assert module is not None
    definition = _definition_manifest()
    selected = [definition["assets"][0], definition["assets"][1]]

    manifest, _, _ = module.build_campaign_wave_manifest(
        chart_id=CHART_ID,
        definition_revision="t0-2026-08-25-corrected-dag",
        definition_manifest=definition,
        definition_manifest_digest=_digest(definition),
        layer="L0",
        wave_index=0,
        candidates=[_candidate(asset) for asset in selected],
        writer_digests={"bg_reference": "a" * 64, "bg_formula_constants": "b" * 64},
        snapshot_ref="cloudsql-backup:backup-1",
    )

    assert manifest["campaign_control"]["definition_revision"] == "t0-2026-08-25-corrected-dag"


@pytest.mark.parametrize(
    ("snapshot_ref", "expected_digest", "message"),
    [
        (None, "a" * 64, "snapshot reference"),
        ("cloudsql-backup:backup-1", None, "preview manifest digest"),
    ],
)
def test_direct_commit_cannot_bypass_snapshot_or_reviewed_preview(
    snapshot_ref: str | None,
    expected_digest: str | None,
    message: str,
) -> None:
    module = _load_dispatch_module()
    assert module is not None

    with pytest.raises(ValueError, match=message):
        module.create_campaign_run(
            database_url="must-not-be-opened",
            chart_id=CHART_ID,
            definition_revision=REVISION,
            layer="L0",
            wave_index=0,
            commit=True,
            snapshot_ref=snapshot_ref,
            expected_manifest_digest=expected_digest,
        )


def test_l0_dispatch_requires_explicit_current_deployment_pin() -> None:
    module = _load_dispatch_module()
    assert module is not None

    with pytest.raises(ValueError, match="reviewed deployed commit SHA"):
        module.create_campaign_run(
            database_url="must-not-be-opened",
            chart_id=CHART_ID,
            definition_revision=REVISION,
            layer="L0",
            wave_index=0,
            commit=False,
        )


def test_dispatches_only_the_ratified_run_id_override() -> None:
    module = _load_dispatch_module()
    assert module is not None
    observed = []

    def run(command, **kwargs):
        observed.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout="execution-456\n", stderr="")

    execution = module.dispatch_campaign_run(
        run_id="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        project="madhav-astrology",
        region="asia-south1",
        job="brahma-build-pipeline-job",
        run_command=run,
    )

    assert execution == "execution-456"
    assert observed[0][0][-2:] == [
        "--async",
        "--format=value(metadata.name)",
    ]
    assert "--args=--run-id,aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee" in observed[0][0]


def test_terminalizes_a_run_when_dispatch_fails_without_acceptance() -> None:
    module = _load_dispatch_module()
    assert module is not None

    class RecordingCursor:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params):
            self.calls.append((" ".join(sql.split()), params))

    cur = RecordingCursor()
    module.terminalize_dispatch_failure(
        cur,
        run_id="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
        error="permission denied",
    )

    assert len(cur.calls) == 1
    sql, params = cur.calls[0]
    assert "UPDATE build_runs SET state='failed'" in sql
    assert "UPDATE build_run_assets SET state='aborted'" in sql
    assert "accept" not in sql.lower()
    assert params[1] == "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"


def test_live_registry_fingerprint_is_insensitive_to_depends_on_array_order() -> None:
    """depends_on is a set; only its ORDER may differ between the stored row and the freeze.

    The TypeScript authority (registryContractFingerprintInput, definitions.ts) sorts
    depends_on before hashing. If this dispatcher hashes the raw stored order, then for any
    asset whose stored array is not already alphabetical no single fingerprint value can
    satisfy both sides: the sorted value makes the dispatcher refuse to dispatch, and the
    unsorted value makes the tracker report permanent contract drift. Measured on L3 at the
    time this test was written, that deadlock covered 15 of 23 ka_* assets while all 23
    matched the frozen manifest under the sorted computation -- i.e. pure array order, no
    semantic contract change anywhere.

    This test fails on the unsorted implementation and passes on the sorted one, so the fix
    has a detector behind it rather than resting on inspection.
    """
    module = _load_dispatch_module()
    if module is None:
        pytest.skip("dispatch script unavailable")

    contract = _contract(sort_order=10, target_table="kala_avadhi")
    ordered = {
        "asset_id": "ka_avadhi",
        "layer": "kala",
        "depends_on": ["ga_positions", "ka_kalasutra", "bg_reference"],
        **contract,
    }
    shuffled = {**ordered, "depends_on": ["ka_kalasutra", "bg_reference", "ga_positions"]}

    assert module._live_registry_fingerprint(
        ordered, campaign_layer="L3"
    ) == module._live_registry_fingerprint(shuffled, campaign_layer="L3")
