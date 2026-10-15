"""K7-4 owner table boundary and anti-regression oracles (DB-free)."""
import copy
import importlib
import json
import ast
from datetime import date
from itertools import permutations
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import services.ka_tulana.ranker as ranker

FROM = "2026-10-13"
TO = "2027-01-11"


def window(identity="A", start="2026-10-20", tier="concurrent", dw=0.62, anchor=30):
    return dict(chart_id="chart", window_id=identity, field_snapshot_id="snapshot",
        window_start=start, window_end="2026-11-30", precision_regime="day_grade",
        confidence_tier=tier, weakest_link="birth_time_robust", robustness={"authority_clean": True},
        event_class="career-event", event_domain="career", lambda_peak=2.0, null_p=0.02,
        factor_informativeness=0.8, factor_consequence=0.3,
        jury=dict(assertion_id="jury:"+identity, generation="candidate:test", dw=dw,
            anchor_days=anchor, null_reason="no_anchor_exposure" if dw is None else None,
            conditional_null={"verdict": "pass", "p_value": 0.1, "denominator": 10}),
        jury_binding=dict(chart_id="chart", window_id=identity, field_snapshot_id="snapshot",
            assertion_id="jury:"+identity, generation="candidate:test"))


def run(*windows, frame=None, preference=None):
    # getattr makes the initial RED a named assertion, not a collection error.
    method = getattr(ranker.KaTulanaService(), "compare_windows", None)
    assert callable(method), "K7-4 typed Pareto comparator is missing"
    return method(list(windows), date_from=FROM, date_to=TO,
        question_frame=frame, preference=preference)


def pair(a, b, **kw):
    run(a,b,**kw)  # RED detects the missing comparator before the compatibility path.
    return ranker.KaTulanaService().compare(a,b,reference_date=FROM,date_to=TO,
        question_frame=kw.get("frame"),preference=kw.get("preference"))


@pytest.mark.parametrize("case,axis,changes,expected", [
    ("N1Tie", "nearest", {"window_start": "2026-10-21"}, "tie"),
    ("N2Win", "nearest", {"window_start": "2026-10-22"}, "A_better"),
    ("DwTie", "strongest", {"jury.dw": 0.60, "jury.anchor_days": 45}, "tie"),
    ("QualificationIgnored", "strongest", {"jury.dw": 0.50, "jury.conditional_null": {"verdict": "insufficient_evidence"}}, "A_better"),
    ("NullNotZero", "strongest", {"jury.dw": 0.0}, "unavailable"),
    ("Unbound", "strongest", {"jury_binding": None}, "unavailable"),
    ("RobustWin", "most_robust", {"confidence_tier": "structural_prior"}, "A_better"),
    ("WeakestIgnored", "most_robust", {"weakest_link": "authority_clean", "robustness": {}}, "tie"),
    ("Stage9Null", "most_robust", {"confidence_tier": None}, "unavailable"),
], ids=lambda x: x if isinstance(x, str) else None)
def test_owner_boundaries(case, axis, changes, expected):
    a, b = window(), window("B")
    if case == "NullNotZero":
        a["jury"]["dw"] = None
        a["jury"]["null_reason"] = "no_anchor_exposure"
    for key, value in changes.items():
        if key.startswith("jury."): b["jury"][key.split(".")[1]] = value
        else: b[key] = value
    result = pair(a, b)
    assert result["axes"][axis]["relation"] == expected, case
    if expected == "unavailable": assert result["relation"] == "incomparable"


def test_OpenElapsed():
    a = window(start="2026-10-01")
    b = window("B", start=FROM)
    c = window("C", start="2026-10-01"); c["window_end"] = "2026-10-10"
    result = run(a, b, c)
    assert result["comparisons"][0]["axes"]["nearest"]["relation"] == "tie"
    assert result["rejected"] == [{"window_id": "C", "reason": "window_elapsed"}]
    assert result["evidence"]["A"]["axes"]["nearest"]["value"] == 0


def test_RelevanceTie_DomainWin_UnknownFrame():
    a, b = window(start="2026-11-01"), window("B", start="2026-11-01")
    b["window_end"] = "2026-12-01"
    assert pair(a, b, frame={"domain": "career"})["axes"]["best_suited"]["relation"] == "tie"
    b["window_end"] = a["window_end"]; b["event_domain"] = "wealth"
    assert pair(a, b, frame={"domain": "career"})["axes"]["best_suited"]["relation"] == "A_better"
    result = run(a,b, frame={"domain": "marriage", "entity": "X", "horizon": "echo"})
    assert result["comparisons"][0]["relation"] == "incomparable"
    assert result["evidence"]["A"]["axes"]["best_suited"]["reason"] == "frame_domain_unknown"
    assert result["entity_not_evaluated"] is True
    assert "best_suited" not in run(a,b)["evidence"]["A"]["axes"]


def tradeoff():
    return window(tier="structural_prior"), window("B", start="2026-11-02", tier="concurrent", dw=0.60, anchor=45)


def test_ParetoWin_TradeoffFront():
    a,b = tradeoff()
    result = run(a,b)
    assert result["comparisons"][0]["relation"] == "incomparable"
    assert result["comparisons"][0]["reason"] == "tradeoff"
    assert set(result["front"]) == {"A", "B"}
    assert result["ordered"] == ["B", "A"]
    a["confidence_tier"] = "concurrent"; b["confidence_tier"] = "structural_prior"
    assert run(a,b)["front"] == ["A"]
    assert pair(a,b)["relation"] == "A_dominates"


def cycle_windows():
    """Binding review K7-B1: each of three different axes supplies one edge."""
    rows = [window("A", FROM, dw=0.0, anchor=25),
            window("B", "2026-10-15", dw=0.03, anchor=25),
            window("C", "2026-10-14", dw=0.06, anchor=25)]
    for row, end in zip(rows, ("2027-01-01", "2027-01-17", "2027-01-20")):
        row["window_end"] = end
    return rows


@pytest.mark.parametrize("extra", ["none", "dominated", "dominator", "both"])
def test_tolerance_cycle_keeps_alternatives_in_every_input_order(extra):
    rows = cycle_windows()
    expected_front = ["A", "B", "C"]
    if extra in {"dominated", "both"}:
        rows.append(window("D", "2026-11-01", tier="structural_prior", dw=-0.3, anchor=25))
    if extra in {"dominator", "both"}:
        superior = window("X", FROM, tier="calibrated", dw=0.8, anchor=25)
        superior["window_end"] = "2027-01-10"
        rows.append(superior)
        expected_front.append("X")
    baseline = None
    for ordering in permutations(rows):
        result = run(*ordering, frame={"domain": "career"})
        assert result["front"] == expected_front, "K7-B1: tolerance cycle lost alternatives"
        assert result["dominance_cycles"] == [["A", "B", "C"]]
        assert result["front_rule"] == "undominated_or_cycle_member"
        assert result["empty_reason"] is None
        assert set(result["ordered"]) == set(result["evidence"])
        assert result == (baseline or result), "input permutation must not change the verdict"
        baseline = result
    relations = {(p["A"], p["B"]): p["relation"] for p in baseline["comparisons"]}
    assert relations[("A", "B")] == "A_dominates"
    assert relations[("B", "C")] == "A_dominates"
    assert relations[("A", "C")] == "B_dominates"
    # Presentation preferences cannot change the graph or protected alternatives.
    preferred = run(*rows, frame={"domain": "career"}, preference=["nearest"])
    for field in ("front", "dominance_cycles", "comparisons", "evidence"):
        assert preferred[field] == baseline[field]


def test_acyclic_multi_candidate_front_and_empty_reason():
    rows = [window("A", FROM, tier="calibrated", dw=0.8),
            window("B", "2026-11-01", tier="concurrent", dw=0.4),
            window("C", "2026-11-10", tier="structural_prior", dw=0.0)]
    for ordering in permutations(rows):
        result = run(*ordering)
        assert result["front"] == ["A"]
        assert result["dominance_cycles"] == []
    for rows in ([], [dict(window(), window_end="2026-10-12", window_start="2026-10-01")]):
        result = run(*rows)
        assert result["front"] == []
        assert result["empty_reason"] == "no_candidate_windows"


def test_Swap():
    a,b = tradeoff()
    ab,ba = pair(a,b),pair(b,a)
    mirror = {"A_better": "B_better", "B_better": "A_better", "tie": "tie", "unavailable": "unavailable"}
    for axis in ab["axes"]:
        assert ba["axes"][axis]["relation"] == mirror[ab["axes"][axis]["relation"]]
        assert ba["axes"][axis]["A"] == ab["axes"][axis]["B"]
    assert pair(window(),window("B"))["relation"] == "tie"
    a, b = window(), window("B", start="2026-11-02", tier="structural_prior")
    assert pair(a, b)["relation"] == "A_dominates"
    assert pair(b, a)["relation"] == "B_dominates"
    a["jury"]["dw"] = None
    a["jury"]["null_reason"] = "no_anchor_exposure"
    assert pair(a, b)["axes"]["strongest"]["A"] == pair(b, a)["axes"]["strongest"]["B"]


def test_Preference_Weights():
    a,b = tradeoff()
    before = copy.deepcopy([a,b])
    default,nearest = run(a,b),run(a,b, preference=["nearest"])
    assert default["ordered"] == ["B", "A"]
    assert nearest["ordered"] == ["A", "B"]
    assert default["evidence"] == nearest["evidence"]
    assert default["comparisons"] == nearest["comparisons"]
    assert [a,b] == before
    assert nearest["order_policy"][0] == "nearest"


def test_Quiet_Contest():
    a,b = window(),window("B")
    a["obstruction"] = {"effective_state": "information_unavailable", "release": None}
    b["obstruction"] = {"effective_state": "evaluated_silent", "release": None}
    a["contest_rows"] = 5  # unbound cannot count
    a["jury_binding"] = None
    result = run(a,b)
    assert result["comparisons"][0]["relation"] == "incomparable"
    assert result["evidence"]["A"]["annotations"]["obstruction"] != result["evidence"]["B"]["annotations"]["obstruction"]
    assert result["evidence"]["A"]["annotations"]["dissonance"] is None
    b["contest_rows"] = 2
    assert run(a,b)["evidence"]["B"]["annotations"]["dissonance"] is True


@pytest.mark.parametrize("preference", [["strongest","strongest"], ["bogus"], ["best_suited"]])
def test_bad_preference_refuses(preference):
    with pytest.raises(ValueError): run(window(), preference=preference)


def test_invalid_horizon_and_mixed_generation_refuse():
    method = getattr(ranker.KaTulanaService(), "compare_windows", None)
    assert callable(method), "K7-4 typed Pareto comparator is missing"
    with pytest.raises(ValueError): method([window()], date_from=FROM, date_to=FROM)
    b=window("B"); b["field_snapshot_id"]="other"
    with pytest.raises(ValueError): run(window(),b)
    b=window("B"); b["jury"]["generation"]="candidate:other"
    with pytest.raises(ValueError): run(window(),b)


def test_no_fixed_weight_import_closure():
    sidecar = Path(__file__).resolve().parents[2]
    pending = [Path(ranker.__file__), sidecar / "services/ka_tulana/__init__.py",
               sidecar / "services/ka_tulana/writer.py"]
    seen = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        source = path.read_text()
        assert "I11_WEIGHTS" not in source and "def _composite" not in source, str(path)
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                imported = sidecar.joinpath(*node.module.split('.')).with_suffix('.py')
                if imported.is_file():
                    pending.append(imported)


def test_selftest_and_writer_false_health(monkeypatch):
    writer = importlib.import_module("services.ka_tulana.writer")
    assert writer._run_selftest()[0]
    method=getattr(ranker.KaTulanaService, "compare_windows", None)
    assert callable(method), "K7-4 typed Pareto comparator is missing"
    def broken(*args, **kw):
        value=method(*args, **kw); value["comparisons"][0]["relation"]="tie"; return value
    monkeypatch.setattr(ranker.KaTulanaService, "compare_windows", broken)
    assert writer._run_selftest()[0] is False
    conn=MagicMock()
    ctx=SimpleNamespace(db_conn=conn, dry_run=False, config={"chart_id":"chart"})
    with pytest.raises(RuntimeError): writer.KaTulanaWriter().run(ctx)
    conn.commit.assert_not_called(); conn.close.assert_not_called()
    assert "asset_throughput" not in str(conn.execute.call_args)


def test_exact_boundary_no_extra_tie_band():
    a, b = window(dw=0.0), window("B", dw=1 / 30 + 1e-16)
    assert pair(a, b)["axes"]["strongest"]["relation"] == "B_better"
    a, b = window(dw=0.62, anchor=30), window("B", dw=0.59, anchor=45)
    result = pair(a, b)
    assert result["axes"]["strongest"]["relation"] == "tie"
    assert result["axes"]["strongest"]["tolerance"] == 1 / 30


def test_stage9_override_and_signed_jury_zero_are_not_recomputed():
    a, b = window(tier="calibrated_provisional", dw=-0.2), window("B", tier="concurrent", dw=0.0)
    result = pair(a, b)
    assert result["axes"]["most_robust"]["relation"] == "A_better"
    assert result["axes"]["strongest"]["relation"] == "B_better"
    assert result["relation"] == "incomparable"
    assert result["reason"] == "tradeoff"


def test_subday_relevance_is_unavailable_and_annotations_do_not_order():
    a, b = window(), window("B")
    a["precision_regime"] = "sub_day"
    assert pair(a, b, frame={})["axes"]["best_suited"]["relation"] == "unavailable"
    a = window()
    before = run(a, b)
    a.update(obstruction={"effective_state": "obstruction_active", "release": None}, contest_rows=20)
    b.update(obstruction={"effective_state": "evaluated_silent", "release": None}, contest_rows=0)
    after = run(a, b)
    assert after["ordered"] == before["ordered"]
    assert after["front"] == before["front"]
    assert after["comparisons"] == before["comparisons"]


def test_jury_coverage_and_provenance_carried_without_qualification_order():
    a = window()
    a["jury"].update(coverage={"state": "evaluated"}, witness_signature=["G-J"],
                     provenance={"fact_ids": ["f1"]})
    annotations = run(a)["evidence"]["A"]["annotations"]
    assert annotations["strongest_coverage"] == {"state": "evaluated"}
    assert annotations["strongest_provenance"] == {"fact_ids": ["f1"]}
    assert annotations["witness_signature"] == ["G-J"]


@pytest.fixture
def tulana_client(monkeypatch):
    import sys
    from types import ModuleType
    import dotenv
    # No .env or credentials are loaded and no DB driver is called.
    monkeypatch.setattr(dotenv, "load_dotenv", lambda: None)
    monkeypatch.setenv("PYTHON_SIDECAR_API_KEY", "fixture-key")
    monkeypatch.setitem(sys.modules, "asyncpg", ModuleType("asyncpg"))
    from fastapi.testclient import TestClient
    import main
    # main may already have been imported by another test during collection.
    # The existing sidecar guard reads this cached value, not the environment.
    monkeypatch.setattr(main, "API_KEY", "fixture-key")
    return TestClient(main.app)


def test_mounted_compute_routes_reject_unauthenticated_requests(tulana_client):
    paths = tulana_client.app.openapi()["paths"]
    assert "/api/compute/tulana_compare" in paths
    for path, operations in paths.items():
        if not path.startswith("/api/compute/"):
            continue
        for method in operations:
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            response = tulana_client.request(method, path, json={})
            assert response.status_code in (401, 403), (method, path, response.status_code)


@pytest.mark.parametrize("headers", [{}, {"x-api-key": ""}, {"x-api-key": "wrong-key"}])
def test_tulana_route_rejects_missing_or_invalid_credentials(tulana_client, headers):
    response = tulana_client.post("/api/compute/tulana_compare", headers=headers,
        json={"windows": [window()], "date_from": FROM, "date_to": TO})
    assert response.status_code in (401, 403)


def test_tulana_route_authenticated_happy_path(tulana_client):
    response = tulana_client.post("/api/compute/tulana_compare",
        headers={"x-api-key": "fixture-key"},
        json={"windows": [window()], "date_from": FROM, "date_to": TO})
    assert response.status_code == 200
    assert response.json()["front"] == ["A"]


def test_authenticated_route_mount_and_validation(tulana_client):
    assert tulana_client.post("/api/compute/tulana_compare", json={"windows": []}).status_code in (401, 403)
    response = tulana_client.post("/api/compute/tulana_compare",
        headers={"x-api-key": "fixture-key"},
        json={"windows": [window()], "date_from": FROM, "date_to": FROM})
    assert response.status_code == 422


def test_allocated_probe_migration_is_the_same_independent_oracle():
    root = Path(__file__).resolve().parents[4]
    migrations = list((root / "platform/migrations").glob("*_k7_4_tulana_pareto_health_probe.sql"))
    assert len(migrations) == 1, "K7-4 allocated probe replacement migration missing"
    source = migrations[0].read_text()
    assert "WHERE asset_id = 'ka_tulana'" in source
    assert source.count("UPDATE asset_registry") == 1
    spec = json.loads(source.split("$hp$")[1])
    from pipeline.orchestrator.service_probes import run_health_probe
    assert run_health_probe("ka_tulana", spec)["status"] == "GREEN"
    spec["expected_relation"] = "tie"
    assert run_health_probe("ka_tulana", spec)["status"] != "GREEN"


def test_immutable_849_contract_runs_a_scoped_nonweighted_compatibility_detector():
    root = Path(__file__).resolve().parents[4]
    source = (root / "platform/migrations/849_nirmana_l3_w3_tulana_health_probe.sql").read_text()
    historical = json.loads(source.split("$hp$")[1])
    from pipeline.orchestrator import service_probes
    validator = getattr(service_probes, "_validated_tulana_probe_config", None)
    assert callable(validator), "immutable migration's historical shape validator must remain available"
    validator(historical)
    result = service_probes.run_health_probe("ka_tulana", historical)
    assert result["status"] == "GREEN"
    assert result["stored_contract_version"] == "849:unversioned"
    assert result["retired_expectations_measured"] is False
    assert "compatibility" in result["scope"]


def test_Mapping_seven_views_hashes_revisions_and_deleted_evidence_refuse():
    service = importlib.import_module("services.ka_tulana")
    mapping = getattr(service, "CERTIFICATION_MAPPING", None)
    assert mapping, "K7-4 certification mapping missing"
    root = Path(__file__).resolve().parents[4]
    validate = service.validate_certification_mapping
    assert validate(root, mapping) == []
    assert set(mapping["views"]) == {"now", "ahead", "priority", "elect", "story", "ritual", "explain"}
    for name, entry in mapping["views"].items():
        assert entry["public_uri"] == f"marsys://tool/L3/kala_{name}_get"
        assert entry["density_contract"]["empty_reason"] is True
        assert entry["fidelity_tests"]
    for mutate in (lambda m: m["views"].pop("now"),
                   lambda m: m["views"]["now"].pop("tier_select"),
                   lambda m: m["views"]["now"].update(fidelity_tests=[]),
                   lambda m: m["hashes"].pop(next(iter(m["hashes"]))),
                   lambda m: m["views"]["now"]["density_contract"].update(empty_reason=False),
                   lambda m: m["hashes"].update({next(iter(m["hashes"])): "0" * 64}),
                   lambda m: m.update(registry_revision=0),
                   lambda m: m["detectors"]["Carr.D2"].update(verdict="PASS")):
        bad = copy.deepcopy(mapping)
        mutate(bad)
        assert validate(root, bad), "invalid certification mapping must refuse the step"
