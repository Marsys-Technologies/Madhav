"""SR-OD1 R8X (PLAN_A10_1 §6; A10.1 B3/B4/B5; TRIAL_READY T16, T18) — the pinned-universe aggregate, the COMPULSORY G-6 sample, and the serial-versus-shards wall rule.

Claims — each has ONE oracle here and the single planted reversion that must make it fail (applied to a copy under the job folder; see result.json):
  T16  the aggregate covers the verifier's PINNED universe (26), never what was attested or what the manifest pins: a one-class or a 25-class generation refuses   — revert: `expected_classes` reads the manifest's list
       (a mixed commit / mixed image generation refuses: test_od1_r8_sharded_aggregate.py a3 / a6, accepted at R8 and unchanged)
  T18a the G-6 SAMPLE is deterministic 3 % of the window keys (the rule of R67's `window_cert_check.g6_sampled`)                                                  — revert: another prefix / another rate
  T18b the generation-wide top five windows by mixed pieces are ALWAYS selected, whatever the sample says (ties by window key; a grain's own top is not enough)       — revert: rank per grain / take four
  T18c the aggregate refuses a generation whose G-6 sample is missing (a selected window with no re-solve, a stale population count)                              — revert: skip the evidence check in the aggregate
  T18d a selected window passes iff the from-scratch re-solve is AGREED; a DISAGREEMENT blocks (the job raises); INCONCLUSIVE / unresolved / another plan is refused  — revert: accept INCONCLUSIVE
  B4   the wall rule: ONE execution iff the serial projection fits 0.75 × 28,800 s, shards only if not; the decision is recorded in the verdict; unmeasured is null   — revert: invert the comparison
Doctrine: §N.8 (a green is computed by a detector that can read false), §N.7.6 (an honest null beats an invented default), A10.1 B3/B4/B5, SR-R8-SHARDED, R67's certificate shape
(`window_solver.stored_certificate`: `geometry.pieces` = [a, b_eff, kind] — kind "mixed" is a piece the solver had to branch-and-bound).
"""
from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import pytest

from services.gochara_kernel import g6_plan
from services.gochara_kernel import input_vector_verifier as ivv
from services.gochara_kernel import numerical_window_gate as nwg
from services.gochara_kernel import verification_job as vj

from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r10_complete_records import CLS, _bypass, _kwargs, _job_position, LIBRA, built, login, rworld  # noqa: F401
from .test_a53_r12_seal_job import built_numbers  # noqa: F401

# G8: the JOB's own census is set aside by name (conftest.g8_census_opt_out) — the world builds one class. The AGGREGATE's universe is NOT: T16 runs against the real pinned universe
# (`G8_AGGREGATE_UNIVERSE = "pinned"`); the G-6 and wall tests narrow it through the file's own seam fixture (`one_class_universe`).
G8_CENSUS_OPT_OUT_REASON = "pinned-universe aggregate, compulsory G-6 sample and wall rule on a deliberate one-class marriage world (SR-OD1 R8X)"
G8_AGGREGATE_UNIVERSE = "pinned"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")

IMAGE = "sha256:" + "1" * 64
EXECUTION = "projects/p/locations/l/jobs/gochara-verification-job/executions/e1"
UNIVERSE = sorted(ivv.SCORED_CLASS_UNIVERSE)


@pytest.fixture(autouse=True)
def _job_identity(monkeypatch):
    monkeypatch.setenv("GOCHARA_RUNNER_IMAGE_DIGEST", IMAGE)
    monkeypatch.setenv("CLOUD_RUN_EXECUTION", EXECUTION)


@pytest.fixture()
def one_class_universe(monkeypatch):
    """The world builds ONE class, and the job itself refuses to re-run over a manifest narrower than the universe (its independent input check re-derives `scored_classes`): so the G-6 and
    wall tests, which re-run the job, take the universe from the classes the world pinned — the seam of the older one-class suites (conftest `g8_census_opt_out`). T16 does NOT."""
    monkeypatch.setattr(nwg, "expected_classes", lambda conn, chart_id, generation, vector: sorted({r[0] for r in conn.execute(
        "SELECT DISTINCT event_class FROM public.ka_gochara_search_path_pin WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchall()}))
    monkeypatch.setattr(nwg, "manifest_vs_universe", lambda vector, universe: [])


def _pin_universe(w, classes):
    _bypass(w, ("UPDATE public.kala_gochara_publication SET input_generation_vector = jsonb_set(input_generation_vector, '{scored_classes}', %s::jsonb)", (json.dumps(list(classes)),)))


def _run_with(w, **extra):
    with login(w, "gochara_verifier") as conn:
        return vj.run(conn, chart_id=CHART_ID, generation=GEN, **_kwargs(w, _job_position(w, [LIBRA])), **extra)


def _agreed(request):
    return SimpleNamespace(classification="AGREED", findings=())


# ── T16 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_t16_the_pinned_universe_is_the_verifiers_own_26():
    assert nwg.pinned_universe() == UNIVERSE and len(UNIVERSE) == 26 == len(set(UNIVERSE))


@pytest.mark.parametrize("pinned", ["attested_only", "twenty_five"])
def test_t16_a_generation_narrower_than_the_pinned_universe_is_refused(built_numbers, pinned):
    """R8's aggregate read the manifest's own list, so a manifest that pinned only what was attested made a one-class generation PASS. The universe is the verifier's: the narrowed manifest is
    named, and every universe class without a pin is a coverage refusal by name."""
    w = built_numbers
    assert _run_with(w)["status"] == "VERIFIED"
    classes = [c for c in UNIVERSE if c != "surgery"] if pinned == "twenty_five" else [CLS]
    _pin_universe(w, classes)
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED"
    assert any(p.startswith("surgery:") and "does not pin" in p and f"it pins {len(classes)})" in p for p in verdict["problems"]), verdict["problems"]
    assert any(p.startswith("surgery:") and "no search-path pin" in p for p in verdict["problems"]), verdict["problems"]       # coverage is judged against the universe, not the attestations
    with pytest.raises(nwg.NumericalGateNotPassed):
        nwg.require_passed(w.conn, CHART_ID, GEN)


# ── T18 (the plan) ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_t18a_the_sample_is_the_deterministic_three_percent_of_the_window_keys():
    def own(key):                                                   # re-derived here from the rule's words, not from the module under test
        return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) / 2 ** 32 < 0.03
    keys = [g6_plan.window_key(CHART_ID, GEN, "marriage", "P3", "1.0.0", f"2030-01-{1 + i % 28:02d}T00:00:00.{i:06d}Z", "2030-02-01T00:00:00.000000Z") for i in range(20000)]
    picked = [k for k in keys if g6_plan.sampled(k)]
    assert picked == [k for k in keys if own(k)] and picked == [k for k in keys if g6_plan.sampled(k)]     # the same windows every time
    assert 0.025 < len(picked) / len(keys) < 0.035                                                          # 3 %, not R67's default 2 %
    assert (g6_plan.SAMPLE_PER_MILLE, g6_plan.SAMPLE_RATE, g6_plan.TOP_MIXED) == (30, 0.03, 5)


def test_t18a_the_sample_rule_is_the_one_of_r67s_g6_sampled():
    """R67's `window_cert_check.g6_sampled` (od1-r67 5a6843bda), which lands before this lane: the plan restates its rule and, once the module is in the tree, equals it at the plan's rate."""
    wcc = pytest.importorskip("services.gochara_kernel.window_cert_check")
    keys = [f"k{i}|{hashlib.sha256(str(i).encode()).hexdigest()}" for i in range(5000)]
    assert [g6_plan.sampled(k) for k in keys] == [wcc.g6_sampled(k, g6_plan.SAMPLE_RATE) for k in keys]


def _w(key, grain, mixed, wid=None):
    return {"key": key, "window_id": wid or key, "grain": grain, "mixed": mixed}


def test_t18b_the_top_five_by_mixed_pieces_are_selected_generation_wide_whatever_the_sample_says():
    g1, g2 = ("marriage", "P3", "1.0.0"), ("career_entry", "P4", "1.0.0")
    wins = [_w(f"a{i}", g1, m) for i, m in enumerate([9, 8, 0, 3, 1])] + [_w(f"b{i}", g2, m) for i, m in enumerate([7, 7, 7, 2, 0])]
    sel = g6_plan.Selection(wins)
    # the five largest over BOTH grains: 9, 8, then the three 7s (ties by window key); a grain's own top is not the generation's
    assert sel.top_mixed == ["a0", "a1", "b0", "b1", "b2"]
    rank = {w["key"]: w["mixed"] for w in wins}
    assert all(g6_plan.BY_TOP in sel.for_grain(w["grain"])[w["key"]]["selected_by"] for w in wins if w["key"] in sel.top_mixed)
    assert "a3" not in sel.for_grain(g1) or g6_plan.BY_TOP not in sel.for_grain(g1)["a3"]["selected_by"]       # sixth and below: only the sample can select them
    assert all(rank[k] > 0 for k in sel.top_mixed)                                                            # a window with no mixed piece is never 'top mixed'
    assert sel.population == {g1: 5, g2: 5}


# ── T18 (the evidence) ────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _evidence_world():
    grain = ("marriage", "P3", "1.0.0")
    sel = g6_plan.Selection([_w("w1", grain, 4, "id1"), _w("w2", grain, 0, "id2")])
    assert sel.for_grain(grain) and "w1" in sel.for_grain(grain)
    return grain, sel, dict(chart_id=CHART_ID, generation=GEN, grain=dict(event_class=grain[0], path_id=grain[1], rule_version=grain[2]), sel=sel)


def test_t18d_a_selected_window_passes_iff_agreed_and_a_disagreement_blocks():
    grain, sel, kw = _evidence_world()
    ok = g6_plan.collect(resolver=_agreed, **kw)
    assert g6_plan.evidence_problems("t", ok, grain, sel) == []
    seen = []
    g6_plan.collect(resolver=lambda req: seen.append(req) or _agreed(req), **kw)
    assert seen and seen[0]["resolve"] is True and seen[0]["window_key"] == "w1" and seen[0]["window_id"] == "id1" and seen[0]["selected_by"] == ["top_mixed"]
    for verdict in ("INCONCLUSIVE", None):                                                       # not settled / not covered by the resolver: not shown, so refused
        ev = g6_plan.collect(resolver=lambda req, v=verdict: None if v is None else SimpleNamespace(classification=v, findings=()), **kw)
        assert any("not AGREED" in p for p in g6_plan.evidence_problems("t", ev, grain, sel)), verdict
    with pytest.raises(RuntimeError, match="DISAGREES"):                                         # a disagreement is not evidence: the job maps it to a DISAGREE and the seal is blocked
        g6_plan.collect(resolver=lambda req: SimpleNamespace(classification="DISAGREEMENT", findings=(("objective_exceeds_stored_maximum", "x"),)), **kw)
    other = dict(ok, plan_digest="0" * 64)                                                       # a verifier that ran another plan
    assert any("not the pinned plan" in p for p in g6_plan.evidence_problems("t", other, grain, sel))
    assert any("no re-solve" in p for p in g6_plan.evidence_problems("t", dict(ok, windows={}), grain, sel))      # a selected window nothing re-solved
    assert any("no G-6 evidence" in p for p in g6_plan.evidence_problems("t", None, grain, sel))


_UTC = "'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'"


def _numbered_windows(w):
    return w.conn.execute(
        "SELECT window_id::text, event_class, path_id, rule_version, to_char(lower(interval) AT TIME ZONE 'UTC', " + _UTC + "), to_char(upper(interval) AT TIME ZONE 'UTC', " + _UTC + ")"
        " FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND peak_instant IS NOT NULL ORDER BY 2, 3, 4, 5, 6, 1", (CHART_ID, GEN)).fetchall()


def _certify(w, monkeypatch):
    """Every NUMBERED window of the world 'carries a certificate' with 1-3 mixed pieces. (This branch predates R67, whose builder stores the certificate in `qualification` and whose
    re-derivation tolerates it; so the population is stood in HERE, and `test_t18e` reads the real stored certificates.)"""
    wins = [{"key": g6_plan.window_key(CHART_ID, GEN, c, pth, v, lo, hi), "window_id": wid, "grain": (c, pth, v), "mixed": 1 + i % 3} for i, (wid, c, pth, v, lo, hi) in enumerate(_numbered_windows(w))]
    assert wins
    monkeypatch.setattr(g6_plan, "population", lambda conn, chart_id, generation: wins)
    return wins


def test_t18c_the_aggregate_refuses_a_generation_whose_g6_sample_is_missing(built_numbers, one_class_universe, monkeypatch):
    w = built_numbers
    assert _run_with(w)["status"] == "VERIFIED"
    assert nwg.generation_verdict(w.conn, CHART_ID, GEN)["status"] == "PASSED"                  # the baseline is clean: no certified window, so the plan selects none
    wins = _certify(w, monkeypatch)                                                              # the certificates arrive: the plan now selects windows the evidence never saw
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED"
    assert any("selected by the G-6 plan but has no re-solve" in p for p in verdict["problems"]), verdict["problems"]
    assert any("certified window(s)" in p for p in verdict["problems"]), verdict["problems"]    # the evidence counted none; the windows now stored say otherwise
    with pytest.raises(nwg.NumericalGateNotPassed):
        nwg.require_passed(w.conn, CHART_ID, GEN)
    # the verifier running the plan WITHOUT a resolver records every selected window unresolved: still refused (nothing here is green unless a re-solve ran and agreed)
    assert _run_with(w)["status"] == "VERIFIED"
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any("is None, not AGREED" in p for p in verdict["problems"]), verdict["problems"]
    # …and with a resolver that AGREES the generation passes; the evidence names every selected window, the aggregate reports the plan
    requests = []
    report = _run_with(w, g6_resolver=lambda req: requests.append(req) or _agreed(req))
    assert report["status"] == "VERIFIED", report["classes"]
    assert requests and all(r["resolve"] and r["chart_id"] == CHART_ID and r["generation"] == GEN for r in requests)
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "PASSED", verdict["problems"]
    g6 = verdict["aggregate"]["g6"]
    assert g6["plan_digest"] == g6_plan.PLAN_DIGEST and g6["sample_per_mille"] == 30 and g6["population"] == len(wins) and len(g6["top_mixed"]) == min(5, len(wins))
    assert {r["window_key"] for r in requests} >= set(g6["top_mixed"])                           # the top-mixed windows were re-solved, whatever the sample said
    assert all(g6_plan.sampled(r["window_key"]) == (g6_plan.BY_SAMPLE in r["selected_by"]) for r in requests)
    # a disagreeing re-solve blocks the class: the run reports DISAGREE at the G-6 stage
    bad = _run_with(w, g6_resolver=lambda req: SimpleNamespace(classification="DISAGREEMENT", findings=(("peak_value_mismatch", "x"),)))
    assert bad["status"] == "DISAGREE" and bad["classes"][CLS]["stage"].startswith("g6_resample"), bad["classes"]


def test_t18e_the_population_is_the_stored_numbered_windows_that_carry_a_certificate(built_numbers):
    w = built_numbers
    assert _run_with(w)["status"] == "VERIFIED"
    assert g6_plan.population(w.conn, CHART_ID, GEN) == []                                       # no stored certificate, no population
    numbered = _numbered_windows(w)
    assert numbered
    # R67's builder stores `qualification.solver_certificate`; this world's 1240 shape check predates that (R67 relaxes it), so the check is lifted for this disposable database
    _bypass(w, ("ALTER TABLE public.ka_gochara_eval_window DROP CONSTRAINT kgew_qualification_shape_ck", ()),
            ("UPDATE public.ka_gochara_eval_window SET qualification = qualification || jsonb_build_object('solver_certificate', jsonb_build_object('geometry', jsonb_build_object("
             "'pieces', '[[0, 1, \"mixed\"], [1, 2, \"up\"], [2, 3, \"mixed\"]]'::jsonb)))", ()))          # on EVERY window, numbered or blank
    pop = g6_plan.population(w.conn, CHART_ID, GEN)
    assert sorted(x["window_id"] for x in pop) == sorted(r[0] for r in numbered)                # blanks (no peak) are not in the population, though they carry one too
    assert all(x["mixed"] == 2 for x in pop)
    assert sorted(x["key"] for x in pop) == sorted(g6_plan.window_key(CHART_ID, GEN, c, pth, v, lo, hi) for _wid, c, pth, v, lo, hi in numbered)


# ── B4 — the wall rule ────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_b4_the_wall_rule_is_serial_iff_the_projection_fits_three_quarters_of_the_timeout():
    assert (nwg.TASK_TIMEOUT_S, nwg.WALL_PERCENT, nwg.BUDGET_S) == (28800, 75, 21600)
    ms = 1000
    fits = nwg.wall_rule({f"c{i}": 5400 * ms for i in range(4)}, 1, 4)                            # 4 classes of 5 400 s: exactly 21 600 s, at the budget: it fits (≤)
    assert (fits["decision"], fits["followed"], fits["problems"], fits["serial_projection_s"]) == ("serial", True, [], 21600)
    assert nwg.wall_rule({"c": 5400 * ms + 1}, 1, 4)["decision"] == "sharded"                      # one millisecond over, per class: out of the budget (exact integer arithmetic)
    two = nwg.wall_rule({"c": 100 * ms}, 2, 26)                                                    # serial fits but it ran as two executions
    assert (two["decision"], two["followed"]) == ("serial", False) and "ONE execution" in two["problems"][0]
    one = nwg.wall_rule({"c": 1000 * ms}, 1, 26)                                                   # 26 000 s: shards are required, and it ran as one
    assert (one["decision"], one["followed"], one["serial_projection_s"]) == ("sharded", False, 26000) and "shards are required" in one["problems"][0]
    shards = nwg.wall_rule({"c": 1000 * ms}, 7, 26)
    assert (shards["decision"], shards["followed"], shards["problems"]) == ("sharded", True, [])
    unknown = nwg.wall_rule({}, 1, 26)                                                             # unmeasured is null, never 'serial'
    assert (unknown["decision"], unknown["followed"], unknown["serial_projection_s"]) == (None, None, None) and unknown["problems"]
    assert not any(isinstance(v, float) for v in fits.values())                                    # the brief is canonical JSON: no float anywhere in the verdict


def _set_wall(w, wall_s, path=None):
    where = "" if path is None else f" WHERE path_id = '{path}'"
    ms = int(wall_s * 1000)
    _bypass(w, (f"UPDATE public.ka_gochara_eval_window_verification SET runner_identity = jsonb_set(runner_identity, '{{verification_wall}}',"
                f" jsonb_build_object('class', 'marriage', 'wall_ms', {ms}, 'lock_wait_ms', 0, 'compute_ms', {ms})){where}", ()))


def _second_execution(w):
    _bypass(w, ("UPDATE public.ka_gochara_eval_window_verification SET runner_identity = jsonb_set(runner_identity, '{verification_shard,execution_id}', to_jsonb('executions/e2'::text))"
                " WHERE path_id = 'P4'", ()))


def test_b4_the_verdict_records_the_wall_rules_decision_and_refuses_a_generation_verified_the_other_way(built_numbers, one_class_universe):
    w = built_numbers
    assert _run_with(w)["status"] == "VERIFIED"
    rows = [r[0] if isinstance(r[0], dict) else json.loads(r[0]) for r in w.conn.execute("SELECT runner_identity FROM public.ka_gochara_eval_window_verification ORDER BY path_id").fetchall()]
    walls = [r[nwg.WALL_KEY] for r in rows]
    assert len(walls) == 4 and len({json.dumps(x, sort_keys=True) for x in walls}) == 1 and walls[0]["class"] == CLS          # one measurement per class, carried by every grain
    assert walls[0]["wall_ms"] == walls[0]["lock_wait_ms"] + walls[0]["compute_ms"] and walls[0]["compute_ms"] > 0 and all(isinstance(v, int) for k, v in walls[0].items() if k != "class")
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    rule = verdict["aggregate"]["wall_rule"]
    assert verdict["status"] == "PASSED" and (rule["decision"], rule["followed"], rule["executions"], rule["budget_s"]) == ("serial", True, 1, 21600)
    # serial fits, yet the rows come from two executions: refused, naming the rule
    _second_execution(w)
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any("ran as 2 executions although the serial projection" in p for p in verdict["problems"]), verdict["problems"]
    # the measured compute (25 000 s for the world's one class) makes the serial projection exceed the budget: now the two executions are what the rule demands, and ONE execution would be the refusal
    _set_wall(w, 25000.0)
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["aggregate"]["wall_rule"]["decision"] == "sharded" and not any("execution" in p and "projection" in p for p in verdict["problems"]), verdict["problems"]
    _bypass(w, ("UPDATE public.ka_gochara_eval_window_verification SET runner_identity = jsonb_set(runner_identity, '{verification_shard,execution_id}', to_jsonb(%s::text))", (EXECUTION,)))
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["status"] == "FAILED" and any("ONE execution although the serial projection" in p for p in verdict["problems"]), verdict["problems"]
    # a row with no measured wall: nothing is concluded (null decision) and the verdict refuses by name
    _bypass(w, ("UPDATE public.ka_gochara_eval_window_verification SET runner_identity = runner_identity - 'verification_wall'", ()))
    verdict = nwg.generation_verdict(w.conn, CHART_ID, GEN)
    assert verdict["aggregate"]["wall_rule"]["decision"] is None and any("carries no measured wall" in p for p in verdict["problems"]), verdict["problems"]


def test_b4_a_class_not_started_by_the_run_has_no_wall():
    """A direct library call (the builder's in-build self-check) is not a measurement: `class_wall` is null for a class `run` did not start, never zero."""
    assert vj.class_wall("never_started") is None
    vj._class_started("c1")
    wall = vj.class_wall("c1")
    assert wall["class"] == "c1" and wall["wall_ms"] >= 0 and wall["wall_ms"] == wall["lock_wait_ms"] + wall["compute_ms"]
    assert vj.class_wall("c2") is None
