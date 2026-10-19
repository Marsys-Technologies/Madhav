"""J-4d slice proofs (SR-EDGES-PROOF b, a-isolation, certification) against the REAL kernel and the pinned ephemeris; no database.

The targets are the SYNTHETIC ray levels of test_j4c_span_edge_polish.CASES (chosen only because the pre-fix edge misses 1 arcsec there; no chart's natal
point). The reference for the tolerance proof is NOT the code under test: `scripts/kala_gochara_cutover/j4d_edge_root.py` reads pyswisseph directly (kernel
flags, scan + bisection) and imports no kernel solver code (asserted below). The pre-fix control is the same one J-4c uses (the Swiss polish of the spline
edge disabled), exposed as `q.prefix_edge_derivation()`.

Claims, each with the single reversion that must make it fail:
  T1 every minted edge is within delta_lambda of the independent root        -> revert the fix (pre-fix derivation): tolerance fails
  T2 a contact with no stated delta_lambda cannot be judged                  -> plant delta_lambda None
  T3 a station-closed edge is judged against the station, not the orb edge  -> plant the same instant 0.5 day off the station
  T4 the independent root shares no code with the solver                     -> plant a kernel import
  I1 fixed vs pre-fix differ only in t_in / t_out                            -> plant a skew of t_exact in the pre-fix run only
  I2 the pre-fix derivation reproduces the golden's own contacts             -> plant a golden t_exact 1 s off
  I3 the arc index (stations, arcs, segments) is untouched by the solve      -> plant a solve that edits the index
  C1 the invented / anomaly detector reads the real certifier's kinds        -> revert the fix: the certifier reads invented + anomaly
"""
from __future__ import annotations

import ast
import dataclasses
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from scripts.kala_gochara_cutover import j4d_edge_root as er
from scripts.kala_gochara_cutover import j4d_slice_qualify as q
from services.gochara_kernel import measuring_capture as mc
from services.gochara_kernel import record_store as rs

from .conftest import EPHE_PATH, requires_swieph
from .test_c49_wrap_cut_support import real_index
from .test_j4c_span_edge_polish import CASES, IDS, _certify, _solve, _utc

pytestmark = requires_swieph
UTC = timezone.utc


def _contacts(edge, occs):
    return [{"contact_id": f"c-{edge.agent}-{n}", "body": edge.agent, "relation_kind": edge.relation, "canonical_target": edge.obj.canonical_target,
             "t_in": o.t_in.isoformat(), "t_out": o.t_out.isoformat(), "t_exact": None if o.t_exact is None else o.t_exact.isoformat(),
             "delta_lambda": o.delta_lambda} for n, o in enumerate(occs)]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_T1_every_minted_edge_is_within_the_stated_delta_lambda_of_the_independent_root_and_the_prefix_edge_is_not(case, monkeypatch):
    edge, occs = _solve(case, polish=True)
    fixed = q.tolerance_proof({"contacts": _contacts(edge, occs)}, case[4], ephe_path=EPHE_PATH)
    assert fixed["passed"], fixed["problems"]
    assert fixed["edges_judged"] > 0 and fixed["max_error_over_delta_lambda"] <= 0.1 and fixed["max_seconds_from_root"] < 0.5
    edge0, occs0 = _solve(case, polish=False, monkeypatch=monkeypatch)
    prefix = q.tolerance_proof({"contacts": _contacts(edge0, occs0)}, case[4], ephe_path=EPHE_PATH)
    assert not prefix["passed"] and prefix["problems"]
    assert all(p.startswith("tolerance_edge_off_ephemeris:") for p in prefix["problems"])


def test_T2_a_contact_without_a_stated_delta_lambda_is_a_problem_and_a_proof_that_judged_nothing_is_not_green():
    case = CASES[0]
    edge, occs = _solve(case, polish=True)
    contacts = _contacts(edge, occs)
    for c in contacts:
        c["delta_lambda"] = None
    got = q.tolerance_proof({"contacts": contacts}, case[4], ephe_path=EPHE_PATH)
    assert not got["passed"] and got["edges_judged"] == 0
    assert any(p.startswith("tolerance_delta_lambda_missing:") for p in got["problems"]) and "tolerance_vacuous: no minted point-contact edge was judged against the ephemeris" in got["problems"]


def test_horizon_clipped_edges_are_counted_not_judged_and_a_ray_less_body_is_a_named_problem():
    case = CASES[0]
    edge, occs = _solve(case, polish=True)
    contacts = _contacts(edge, occs)
    horizon = case[4]
    contacts[0]["t_in"] = horizon[0].isoformat()
    got = q.tolerance_proof({"contacts": contacts}, horizon, ephe_path=EPHE_PATH)
    assert got["edge_classes"].get("horizon_clip", 0) >= 1 and got["passed"]
    node = dict(contacts[0], body="rahu", contact_id="node", t_in=_utc(2007, 11, 1).isoformat())
    assert q.tolerance_proof({"contacts": [node]}, horizon, ephe_path=EPHE_PATH)["problems"][0].startswith("tolerance_no_ray_level: node")


def test_T3_a_span_closed_at_a_station_is_judged_against_the_station_and_the_same_level_half_a_day_off_it_is_not():
    sky = er.Sky(EPHE_PATH)
    jd0 = datetime(2002, 10, 7, tzinfo=UTC).timestamp() / 86400.0 + 2440587.5             # Mercury turns retrograde that day (the ephemeris speed changes sign; measured)
    station = er.station_root(sky, "mercury", jd0)
    assert station is not None and abs(sky.state("mercury", station)[1]) < 1e-4
    level = (sky.lon("mercury", station) - 1.0) % 360.0                                    # the band edge (orb 1 degree) touches the station: a tangent, no sign change
    at = er.check_edge(sky, "mercury", station, [level], 1.0, 0.000278)
    assert at["class"] in ("station_closed", "orb_edge") and at["error_deg"] <= 0.000278
    off = er.check_edge(sky, "mercury", station + 0.5, [level], 1.0, 0.000278)
    assert off["class"] == "unverified"


def test_T4_the_independent_root_imports_nothing_from_the_kernel_or_the_harness():
    tree = ast.parse(Path(er.__file__).read_text(encoding="utf-8"))
    imported = {n.module if isinstance(n, ast.ImportFrom) else a.name for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))
                for a in (n.names if isinstance(n, ast.Import) else [n])}
    assert {m for m in imported if m} <= {"__future__", "swisseph"}, imported


# ── solver isolation ────────────────────────────────────────────────────────────────────────────────────────────────

HORIZON = (_utc(2002, 10, 1), _utc(2008, 3, 1))        # one horizon for the golden and the proof (the proof takes the golden's single horizon)
ISO_CASES = [CASES[0][:4] + (HORIZON,) + CASES[0][5:], CASES[4][:4] + (HORIZON,) + CASES[4][5:]]       # a slow (jupiter) and a fast (mercury) body


def _golden_from_prefix(monkeypatch):
    """The OLD golden: the pre-fix derivation's contacts, as the measuring build stored them (independent of the proof under test: J-4c's own solve)."""
    contacts, records = [], []
    for case in ISO_CASES:
        edge, occs = _solve(case, polish=False, monkeypatch=monkeypatch)
        monkeypatch.undo()
        for c in _contacts(edge, occs):
            c["contact_id"] = str(occs[int(c["contact_id"].rsplit("-", 1)[1])].contact.contact_id)
            contacts.append(c)
            records.append(mc.golden_record({
                "record_id": "r", "event_class": "marriage", "affected_person": "native", "frame_kind": "lagna", "frame_arg": None, "agent": c["body"],
                "relation": c["relation_kind"], "object_id": "o", "object_role": "signature_house", "contact_id": c["contact_id"], "path_id": "P3",
                "rule_version": "1.0.0", "prerequisites": [], "source_text": None, "period_anchor_lord": None, "period_anchor_level": None,
                "admission_state": "admitted", "operator_role": "scored", "temporal_support_intervals": [[c["t_in"], c["t_out"]]]}))
    return {"records": records, "contacts": contacts, "windows": []}


def _index_for(body):
    return real_index(body)


def _isolation(golden, index_for=_index_for):
    return q.solver_isolation_proof(golden, ["marriage"], HORIZON, ephe_path=EPHE_PATH, index_for=index_for)


def test_I1_the_fixed_solver_moves_only_the_edges_and_the_prefix_derivation_reproduces_the_golden(monkeypatch):
    got = _isolation(_golden_from_prefix(monkeypatch))
    assert got["passed"], got["problems"]
    assert got["obligations"] == 2 and got["golden_contacts_reproduced_by_prefix"] == got["occurrences_solved"] > 0
    assert got["edges_fixed_vs_prefix"]["moved"] > 0 and got["edges_fixed_vs_prefix"]["max_seconds"] > 0           # the fix really moved edges here: the proof is not comparing a thing with itself
    assert sorted(got["bodies_fingerprinted"]) == ["jupiter", "mercury"] and all(len(v) == 12 for v in got["arc_index_fingerprints"].values())


def test_I1_planted_the_pre_fix_run_skews_t_exact(monkeypatch):
    golden = _golden_from_prefix(monkeypatch)
    real_find = rs.find_roots
    original = rs._refine_root

    def skewed(index, body, relation, lam, ephe_path=None, refine=True):
        roots = real_find(index, body, relation, lam, ephe_path, refine=refine)
        return roots if rs._refine_root is original else [dataclasses.replace(r, exact_jd=r.exact_jd + 1e-4) for r in roots]
    monkeypatch.setattr(rs, "find_roots", skewed)
    got = _isolation(golden)
    assert not got["passed"] and any(p.startswith("isolation_fields_other_than_edges_differ:") for p in got["problems"])


def test_I2_a_golden_that_the_prefix_derivation_cannot_reproduce_fails(monkeypatch):
    golden = _golden_from_prefix(monkeypatch)
    victim = golden["contacts"][0]
    victim["t_exact"] = (datetime.fromisoformat(victim["t_exact"]) + timedelta(seconds=1)).isoformat()
    got = _isolation(golden)
    assert not got["passed"] and [p.split(":")[0] for p in got["problems"]] == ["isolation_golden_not_reproduced_by_prefix_derivation"]


def test_I3_a_solve_that_edits_the_arc_index_fails_the_fingerprint(monkeypatch):
    golden = _golden_from_prefix(monkeypatch)
    real_solve = rs.solve_point_edges

    def editing(edges, *, arc_index_for, **kw):
        out = real_solve(edges, arc_index_for=arc_index_for, **kw)
        arc_index_for("x").stations.append(0.0)               # a station invented in place
        return out
    monkeypatch.setattr(rs, "solve_point_edges", editing)
    got = _isolation(golden, index_for=lambda body: dataclasses.replace(real_index(body), stations=list(real_index(body).stations)))
    assert not got["passed"] and {p.split(":")[0] for p in got["problems"]} == {"isolation_arc_index_changed"}


def test_an_isolation_proof_with_no_point_obligation_is_not_green():
    got = q.solver_isolation_proof({"records": [], "contacts": [], "windows": []}, ["marriage"], (_utc(2007, 10, 15), _utc(2008, 3, 1)), ephe_path=EPHE_PATH, index_for=_index_for)
    assert not got["passed"] and got["problems"] == ["isolation_vacuous: no golden point obligation was re-solved"]


# ── the invented / anomaly detector reads the real certifier ────────────────────────────────────────────────────────

@pytest.mark.parametrize("case", [c for c in CASES if c[5]], ids=[i for c, i in zip(CASES, IDS) if c[5]])
def test_C1_the_certifier_counts_zero_invented_zero_anomaly_for_the_fixed_edges_and_reads_the_prefix_ones_as_defects(case, monkeypatch):
    edge, occs = _solve(case, polish=True)
    clean = q.count_certification(_certify(case, edge, occs))
    assert clean["stretches"] > 0 and clean["invented"] == 0 and clean["anomaly"] == 0
    edge0, occs0 = _solve(case, polish=False, monkeypatch=monkeypatch)
    dirty = q.count_certification(_certify(case, edge0, occs0))
    assert dirty["invented"] >= 1 and dirty["anomaly"] >= 1
