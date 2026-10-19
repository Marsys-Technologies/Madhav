"""VC-2 oracles for the arm generator (pure core, no database).

Each test measures ONE production claim from the sealed pre-registration
(`KSHETRA_ABLATION_PREREGISTRATION_v1_1.md`, NR-KALA-R12) with the rule re-derived here from the
declaration text, never from the code's own output. All chart-like values are synthetic fixtures;
nothing here is a chart fact, an outcome, a score or a baseline.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SRC = Path(os.environ.get("VC2_SRC_DIR", ROOT / "platform/scripts/value_checkpoint"))
sys.path.insert(0, str(SRC))
core = importlib.import_module("vc2_core")
run = importlib.import_module("vc2_run")

VC = ROOT / "00_ARCHITECTURE/briefs/l3_families/value_checkpoint"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
SENTINEL = "SENTINEL_OUTCOME_TEXT_DO_NOT_LEAK"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ------------------------------------------------------------------ synthetic fixtures

def chapters(n=9, start=date(1984, 1, 1), years=(7, 20, 6, 10, 7, 18, 16, 19, 17)):
    out, cursor = [], start
    for i in range(n):
        end = cursor + timedelta(days=int(years[i % 9] * 365))
        out.append({"ref": f"md{i}", "lord": f"L{i}", "start": cursor.isoformat(), "end": end.isoformat()})
        cursor = end
    return out


def coverage(chs, first=0, last=None):
    last = len(chs) - 1 if last is None else last
    return {"ref": "synthetic-cov", "start": chs[first]["start"], "end": chs[last]["end"]}


def sources(cls="c0"):
    return {"sangam": [{"window": "w1", "start": "1990-03-01T00:00:00Z", "end": "1990-09-01T00:00:00Z",
                        "effect": 0.5, "null_verdict": "pass", "witnesses": ["G-P", "G-T"]}],
            "taranga": [{"month": "1990-03-01", "integral": 0.25}, {"month": "1990-04-01", "integral": 0.5}],
            "segments": [{"index": 0, "start": "1990-03-01T00:00:00Z", "end": "1990-06-01T00:00:00Z", "alpha": -2.5,
                          "gamma": 0.001, "integral_days": 0.3, "promise": 0.6, "clock": 0.2, "modifier": 0.1,
                          "suppression": 0.9, "weakest_link": "clock"}]}


def snapshot(chs=None, events=(), srcs=None, classes=("c0",)):
    chs = chs or chapters()
    return {"chart_id": CHART, "generation": "candidate:synthetic", "chapters": chs, "events": list(events),
            "lel_coverage": coverage(chs), "synthetic": True, "evaluation_eligible": False, "pins": {},
            "sources": srcs if srcs is not None else {c: sources(c) for c in classes}}


def klass(name="c0", **kw):
    return dict({"event_class": name, "prior_provenance": "synthetic-fixture", "calibrated": True,
                 "synthetic_prior": False}, **kw)


def generate(snap=None, classes=None, mode="rehearsal"):
    snap = snap or snapshot()
    return core.generate(snap, classes or [klass()], core.protocol_pins(), mode)


def manifest(files):
    return json.loads(files["manifest.json"])


# ------------------------------------------------------------------ C1 seed

def test_seed_is_first_eight_hex_digits_of_protocol_sha256():
    """prereg §3: seed = first eight hex digits of the PROTOCOL SHA-256, as an unsigned integer."""
    protocol_hex = hashlib.sha256((VC / "preregistration.json").read_bytes()).hexdigest()
    pins = core.protocol_pins()
    assert pins["seed"] == int(protocol_hex[:8], 16)
    assert pins["protocol_sha256"] == protocol_hex
    assert pins["declaration_sha256"] == hashlib.sha256((VC / core.DECLARATION).read_bytes()).hexdigest()
    assert pins["seed"] != int(pins["declaration_sha256"][:8], 16)


# ------------------------------------------------------------------ C2 selection

def _hash(i):
    return hashlib.sha256(f"{CHART}|{i}".encode()).hexdigest()


def _eligible(counts):
    return [{"pair_index": i, "lel_event_count": c, "hash": _hash(i)} for i, c in enumerate(counts)]


def test_selection_reserves_lowest_hash_ordinary_pair_before_filling_by_hash():
    """prereg §3: first reserve the lowest-hash ordinary candidate, then fill remaining slots in hash order."""
    ranked = sorted(range(12), key=lambda i: (_hash(i), i))
    counts = [100 + i for i in range(12)]
    # the three worst-hash pairs carry the three lowest counts: ordinary = {ranks 9,10,11}
    for position, i in enumerate(ranked[9:]):
        counts[i] = position
    result = core.select_pairs(CHART, _eligible(counts))
    chosen = {p["pair_index"] for p in result["selected"]}
    reserved = ranked[9]  # best hash among the ordinary candidates
    assert len(chosen) == core.MAX_PAIRS == 8
    assert chosen == {reserved} | set(ranked[:7])
    assert [p["pair_index"] for p in result["selected"] if p["reserved_ordinary"]] == [reserved]
    assert result["selected"] == sorted(result["selected"], key=lambda p: p["pair_index"])


# ------------------------------------------------------------------ C3 quartile

def test_ordinary_threshold_is_nearest_rank_lower_quartile_with_ties():
    """prereg §3: sorted counts, one-based rank ceil(0.25 N), 'at or below' so ties are included."""
    for counts in ([3, 9, 3, 3, 5, 6, 7, 3], [1, 2, 3, 4, 5, 6, 7, 8, 9], [4, 4, 4, 4], [5]):
        rank = math.ceil(0.25 * len(counts))
        assert core.ordinary_threshold(counts) == sorted(counts)[rank - 1]
    result = core.select_pairs(CHART, _eligible([3, 9, 3, 3, 5, 6, 7, 3]))
    assert {p["pair_index"] for p in result["selected"] if p["ordinary"]} == {0, 2, 3, 7}


# ------------------------------------------------------------------ C4 eligibility

def test_pairs_need_both_chapters_inside_lel_coverage():
    """prereg §3: only adjacent pairs whose two chapters are fully inside the documented LEL span."""
    chs = chapters()
    pairs = core.enumerate_pairs(CHART, chs, coverage(chs, first=2, last=6), [])
    assert [p["pair_index"] for p in pairs] == [2, 3, 4, 5]


def test_event_counts_use_half_open_bounds_and_unique_ids():
    """prereg §3: boundary instants belong to the later chapter; counts are unique LEL event identities."""
    chs = chapters()
    start, boundary, end = chs[1]["start"], chs[1]["end"], chs[2]["end"]
    events = [{"event_id": "e-start", "date": start}, {"event_id": "e-boundary", "date": boundary},
              {"event_id": "e-end", "date": end},  # belongs to chapter 3, outside pair (1,2)
              {"event_id": "e-dup", "date": boundary}, {"event_id": "e-dup", "date": boundary}]
    pair = [p for p in core.enumerate_pairs(CHART, chs, coverage(chs), events) if p["pair_index"] == 1][0]
    assert pair["lel_event_count"] == 3  # start, boundary, one e-dup; the end date is excluded
    after = [p for p in core.enumerate_pairs(CHART, chs, coverage(chs), events) if p["pair_index"] == 2][0]
    # pair (2,3) starts on the shared boundary: e-boundary, e-dup and the pair-(1,2) end date e-end all fall inside it
    assert after["lel_event_count"] == 3


def test_no_eligible_pair_is_insufficient_evidence_with_no_units():
    """prereg §3: no eligible or ordinary pair => insufficient_evidence, no dramatic-pair substitute."""
    chs = chapters()
    snap = snapshot(chs)
    snap["lel_coverage"] = {"ref": "tiny", "start": chs[0]["start"], "end": chs[0]["end"]}
    files = generate(snap)
    m = manifest(files)
    assert m["selection"]["status"] == "insufficient_evidence" and m["units"] == []
    assert not [p for p in files if p.startswith(("arms/", "judge_packet/"))]


# ------------------------------------------------------------------ C5 blinding

def _reference_permutation(seed, key, items):
    """Re-derivation of PRNG_ID sha256-counter-fisher-yates/1 from its name and the declaration's seed rule."""
    def stream():
        counter = 0
        while True:
            block = hashlib.sha256(f"{seed}|{key}|{counter}".encode()).digest()
            for offset in range(0, 32, 8):
                yield int.from_bytes(block[offset:offset + 8], "big")
            counter += 1
    values, draws = list(items), stream()
    for position in range(len(values) - 1, 0, -1):
        n = position + 1
        bound = (1 << 64) - ((1 << 64) % n)
        draw = next(draws)
        while draw >= bound:
            draw = next(draws)
        values[position], values[draw % n] = values[draw % n], values[position]
    return values


def test_order_map_is_the_pinned_seeded_permutation_per_pair():
    """prereg §3: P/Q/R labels, seeded, PRNG implementation pinned (not the interpreter's shuffle)."""
    seed = core.protocol_pins()["seed"]
    seen = set()
    for pair_index in range(30):
        mapping = core.order_map(seed, CHART, pair_index)
        assert list(mapping) == ["P", "Q", "R"]
        assert sorted(mapping.values()) == sorted(core.ARMS)
        assert list(mapping.values()) == _reference_permutation(seed, f"{CHART}|{pair_index}", core.ARMS)
        seen.add(tuple(mapping.values()))
    assert len(seen) > 1


def test_judge_packet_hides_arm_identity_and_sealed_map_matches_manifest():
    """prereg §3/§4: judges get only P/Q/R; the map is sealed separately and committed by hash."""
    files = generate()
    judge = [p for p in files if p.startswith("judge_packet/")]
    assert judge
    for path in judge:
        if path.endswith("RUBRIC.json"):
            continue
        assert Path(path).stem in core.LABELS
        text = files[path].decode()
        assert "A_prime" not in text and "arms/" not in path
    assert manifest(files)["order_map_sha256"] == sha(files["sealed/order_map.json"])
    assert not any(p.startswith("sealed/") for p in judge)
    mapping = json.loads(files["sealed/order_map.json"])
    some = next(iter(mapping.values()))
    packet_to_arm = {label: core.render_body(arm, _unit_for(files)) for label, arm in some.items()}
    for label, body in packet_to_arm.items():
        unit_dir = next(p for p in files if p.startswith("judge_packet/") and p.endswith(f"/{label}.txt"))
        assert files[unit_dir].decode().endswith(body)


def _unit_for(files):
    m = manifest(files)
    pair = m["selection"]["selected"][0]
    snap = snapshot()
    return {"pair": pair, "event_class": "c0", "data": core.build_unit_data(pair, snap["sources"]["c0"])}


# ------------------------------------------------------------------ C6 matched information

def _section_lines(body, name):
    lines = body.splitlines()
    start = lines.index(f"SECTION\t{name}")
    out = []
    for line in lines[start + 1:]:
        if line.startswith("SECTION\t"):
            break
        out.append(line)
    return out


def test_arms_share_scaffold_and_differ_only_by_registered_additions():
    """prereg §3: same layout and shared information; A ⊂ A′ ⊂ B, each adding exactly its registered section."""
    files = generate()
    unit = manifest(files)["units"][0]["unit_id"]
    body = {a: files[f"arms/{unit}/{a}.txt"].decode() for a in core.ARMS}
    scaffold = lambda t: [l for l in t.splitlines() if l.startswith(("PAIR", "CHAPTER", "CLASS", "SECTION", "COLUMNS"))]
    assert scaffold(body["A"]) == scaffold(body["A_prime"]) == scaffold(body["B"])
    sangam = _section_lines(body["A"], "SANGAM_WINDOWS")
    assert sangam == _section_lines(body["A_prime"], "SANGAM_WINDOWS") == _section_lines(body["B"], "SANGAM_WINDOWS")
    assert any(l.startswith("ROW") for l in sangam)
    unavailable = lambda section: [f"COLUMNS\t" + "\t".join(core.COLUMNS[section]), "UNAVAILABLE\tnot_in_this_arm"]
    assert _section_lines(body["A"], "MONTHLY_WAVEFORM") == unavailable("MONTHLY_WAVEFORM")
    assert _section_lines(body["A"], "TRAJECTORY_SEGMENTS") == unavailable("TRAJECTORY_SEGMENTS")
    assert _section_lines(body["A_prime"], "TRAJECTORY_SEGMENTS") == unavailable("TRAJECTORY_SEGMENTS")
    assert _section_lines(body["A_prime"], "MONTHLY_WAVEFORM") == _section_lines(body["B"], "MONTHLY_WAVEFORM")
    assert any(l.startswith("ROW") for l in _section_lines(body["B"], "TRAJECTORY_SEGMENTS"))


# ------------------------------------------------------------------ C7 budget

def _fat_segments(n):
    base = sources()["segments"][0]
    return [dict(base, index=i) for i in range(n)]


def test_word_ceiling_is_equal_and_overflow_is_not_evaluable_never_truncated():
    """prereg §3: 1,200 whitespace words per arm per pair; overflow => not_evaluable, no selective truncation."""
    assert core.WORD_CEILING == json.loads((VC / "preregistration.json").read_text())["presentation"]["max_words_per_arm_pair"]
    srcs = {"c0": dict(sources(), segments=_fat_segments(120))}  # 12 words/segment: only arm B overflows
    files = generate(snapshot(srcs=srcs))
    m = manifest(files)
    unit = [u for u in m["units"]][0]
    assert unit["status"] == "not_evaluable" and unit["reason"] == "budget_overflow:B"
    assert unit["words"]["B"] > core.WORD_CEILING >= unit["words"]["A"]
    assert not [p for p in files if p.startswith(("arms/", "judge_packet/")) and unit["unit_id"] in p]
    # exactly at the ceiling still renders (<=), counted on the words actually shown
    ok = generate(snapshot(srcs={"c0": dict(sources(), segments=_fat_segments(10))}))
    unit_ok = manifest(ok)["units"][0]
    assert unit_ok["status"] == "ok"
    for arm in core.ARMS:
        assert unit_ok["words"][arm] == len(ok[f"arms/{unit_ok['unit_id']}/{arm}.txt"].decode().split())


# ------------------------------------------------------------------ C8 reproducibility

def test_second_run_is_byte_identical_and_independent_of_source_row_order():
    """tests row 1: outputs are byte-identical on a second run, whatever order the database returns rows."""
    first = generate()
    assert first == generate()
    snap = snapshot()
    src = snap["sources"]["c0"]
    src["sangam"] = src["sangam"] + [dict(src["sangam"][0], window="w0", start="1990-01-15T00:00:00Z",
                                          end="1990-02-15T00:00:00Z")]
    in_order = generate(snap)
    snap2 = snapshot()
    src2 = snap2["sources"]["c0"]
    src2["sangam"] = list(reversed(src["sangam"]))
    src2["taranga"] = list(reversed(src2["taranga"]))
    assert in_order == generate(snap2)


def test_repro_digest_changes_with_any_byte_or_file():
    files = generate()
    base = core.repro_digest(files)
    flipped = dict(files)
    path = next(p for p in files if p.startswith("arms/"))
    flipped[path] = files[path][:-1] + b"X"
    assert core.repro_digest(flipped)["digest"] != base["digest"]
    assert core.repro_digest(dict(files, extra=b"x"))["digest"] != base["digest"]
    assert core.repro_digest(dict(reversed(list(files.items()))))["digest"] == base["digest"]


# ------------------------------------------------------------------ C9 gate

@pytest.fixture
def freeze(tmp_path):
    receipt = tmp_path / "G1_BASELINE.json"
    receipt.write_text(json.dumps({"schema": "ky.g1_baseline/1", "merged_head": "a" * 40, "code_digest": "b" * 64}))
    pins = core.protocol_pins()
    binding = {"G1_head_sha": "a" * 40, "G1_code_digest": "b" * 64, "preregistration_commit": "c" * 40,
               "declaration_sha256": pins["declaration_sha256"], "protocol_sha256": pins["protocol_sha256"],
               "baseline_receipt_sha256": sha(receipt.read_bytes()), "tracker_event_ref": "synthetic-event-1"}
    path = tmp_path / "VC_BINDING.json"
    path.write_text(json.dumps(binding))
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    (outputs / "README.md").write_text("placeholder")
    elig = {"chart_id": CHART, "synthetic": False, "evaluation_eligible": True, "real_outcome_records": True,
            "consent_ref": "synthetic-consent-ref", "lel_coverage": {"ref": "r", "start": "1990-01-01", "end": "2020-01-01"},
            "classes": [{"event_class": f"c{i}", "prior_provenance": "p", "calibrated": True, "synthetic_prior": False}
                        for i in range(6)]}

    def show(commit, rel):
        return (ROOT / rel).read_bytes()

    def reasons(**over):
        kw = dict(receipt_path=receipt, binding_path=path, eligibility=elig, outputs_dir=outputs, show=show)
        kw.update(over)
        return core.check_readiness(**kw)
    return type("F", (), {"reasons": staticmethod(reasons), "receipt": receipt, "binding": path, "outputs": outputs,
                          "elig": elig, "tmp": tmp_path, "pins": pins})


def test_complete_freeze_is_ready(freeze):
    assert freeze.reasons() == []


def test_absent_g1_receipt_refuses(freeze):
    """prereg §2: no accepted G1 receipt => no VC-2 READY (the real receipt is absent at preparation)."""
    assert "g1_receipt_absent_or_unreadable" in freeze.reasons(receipt_path=freeze.tmp / "missing.json")


def test_binding_must_match_the_receipt_bytes_head_and_code_digest(freeze):
    """prereg §2 step 2: baseline_receipt_sha256 is the hash of the receipt's raw bytes."""
    freeze.receipt.write_text(json.dumps({"schema": "ky.g1_baseline/1", "merged_head": "a" * 40,
                                          "code_digest": "b" * 64, "note": "edited after binding"}))
    assert "binding_receipt_hash_differs_from_receipt_bytes" in freeze.reasons()


def test_binding_must_match_declaration_files_and_the_landed_commit(freeze):
    """prereg §2: declaration/protocol hashes equal the raw files AND the content at the landing commit."""
    assert "landed_commit_content_differs_from_binding" in freeze.reasons(show=lambda c, r: b"other bytes")
    bad = json.loads(freeze.binding.read_text())
    bad["protocol_sha256"] = "d" * 64
    freeze.binding.write_text(json.dumps(bad))
    assert "binding_protocol_hash_differs_from_files" in freeze.reasons()


def test_preexisting_outputs_invalidate_the_run(freeze):
    """prereg §2: existing outputs invalidate that run; real generation needs an empty outputs directory."""
    (freeze.outputs / "arms").mkdir()
    (freeze.outputs / "arms" / "x.txt").write_text("early")
    assert "preexisting_outputs_invalidate_run" in freeze.reasons()


@pytest.mark.parametrize("change,reason", [
    ({"synthetic": True}, "synthetic_chart_refused"),
    ({"evaluation_eligible": False}, "evaluation_eligible_not_true"),
    ({"consent_ref": ""}, "consent_reference_absent"),
    ({"chart_id": "00000000-0000-0000-0000-000000000001"}, "chart_outside_canonical_scope"),
    ({"classes": []}, "six_distinct_class_identities_required"),
])
def test_ineligible_population_refuses(freeze, change, reason):
    """prereg §3: consent + real outcomes + evaluation_eligible, canonical chart only, never synthetic."""
    assert reason in freeze.reasons(eligibility=dict(freeze.elig, **change))


def test_synthetic_or_unprovenanced_class_priors_refuse(freeze):
    classes = [dict(c) for c in freeze.elig["classes"]]
    classes[0]["synthetic_prior"] = True
    assert "class_prior_provenance_absent_or_synthetic" in freeze.reasons(eligibility=dict(freeze.elig, classes=classes))


# ------------------------------------------------------------------ C10 no outcome leakage

def test_no_outcome_text_reaches_any_output():
    """prereg §3/§4: outcomes are for selection/coverage only, never model input or judge context."""
    chs = chapters()
    events = [{"event_id": "e1", "date": chs[1]["start"], "description": SENTINEL, "category": SENTINEL,
               "outcome_observed": True}]
    files = generate(snapshot(chs, events=events))
    assert manifest(files)["selection"]["eligible"][1]["lel_event_count"] == 1
    for path, data in files.items():
        assert SENTINEL.encode() not in data, path
        assert b'"e1"' not in data, path


# ------------------------------------------------------------------ C11 outputs location

def test_rehearsal_never_writes_under_committed_outputs_and_real_only_there(tmp_path, monkeypatch):
    """prereg §2: preexisting outputs invalidate a run, so rehearsal output must stay out of outputs/."""
    committed = tmp_path / "outputs"
    monkeypatch.setattr(run, "OUTPUTS_DIR", committed.resolve())
    files = {"x.txt": b"x"}
    with pytest.raises(run.Refused):
        run.write_files(files, committed / "nested", "rehearsal")
    assert not committed.exists()
    with pytest.raises(run.Refused):
        run.write_files(files, tmp_path / "elsewhere", "real")
    run.write_files(files, committed, "real")
    assert (committed / "x.txt").read_bytes() == b"x"
    with pytest.raises(run.Refused):
        run.write_files(files, committed, "real")  # destination already holds outputs


# ------------------------------------------------------------------ C12 lane guard

@pytest.mark.parametrize("dsn", [
    "postgresql://u@db.example.com:55433/ky_x",
    "postgresql://u@127.0.0.1:5432/ky_x",
    "postgresql://u@127.0.0.1:55433/postgres",
    "postgresql://u@127.0.0.1:55433/ky_x?host=db.example.com",
    "postgresql://u@127.0.0.1:55433,db.example.com:55433/ky_x",
])
def test_only_the_loopback_lane_cluster_is_reachable(dsn):
    """Job header: never a production or remote database; lane cluster 127.0.0.1:55433, ky_* databases."""
    with pytest.raises(run.Refused):
        run.assert_lane_dsn(dsn)
    assert run.assert_lane_dsn("postgresql://postgres@127.0.0.1:55433/ky_vc2_abc") == "ky_vc2_abc"


# ------------------------------------------------------------------ C13 unavailable inputs

def test_unavailable_arm_input_is_not_evaluable_but_searched_empty_is_reported_as_none():
    """prereg §3: an unavailable required arm is not an empty/quiet result."""
    srcs = {"c0": dict(sources(), sangam=None), "c1": dict(sources(), taranga=[], sangam=[])}
    files = generate(snapshot(srcs=srcs, classes=("c0", "c1")), [klass("c0"), klass("c1")])
    units = {u["event_class"]: u for u in manifest(files)["units"]}
    assert units["c0"]["status"] == "not_evaluable" and units["c0"]["reason"] == "arm_input_unavailable:sangam"
    assert units["c1"]["status"] == "ok"
    assert "NONE\tnone_in_span" in files[f"arms/{units['c1']['unit_id']}/A.txt"].decode()
    assert not [p for p in files if units["c0"]["unit_id"] in p]


def test_synthetic_or_uncalibrated_class_prior_makes_the_class_not_evaluable():
    """prereg §3: missing identities or priors make the class not evaluable; G1 itself is not 'calibrated'."""
    files = generate(classes=[klass("c0", synthetic_prior=True)])
    unit = manifest(files)["units"][0]
    assert unit["status"] == "not_evaluable" and unit["reason"] == "class_prior_not_calibrated_or_unprovenanced"
    files = generate(classes=[klass("c0", calibrated=False)])
    assert manifest(files)["units"][0]["status"] == "not_evaluable"


# ------------------------------------------------------------------ C14 nobody scores

def test_nothing_is_scored_or_adjudicated_by_the_generator():
    """Item title: outputs only; the manifest carries null scores and verdict, and no scoring field."""
    m = manifest(generate())
    assert m["actual_scores"] is None and m["actual_verdict"] is None
    flat = json.dumps(m)
    for forbidden in ("\"score\"", "\"verdict\":", "dimension_scores"):
        assert forbidden not in flat
    assert m["mode"] == "rehearsal" and m["synthetic"] is True


# ------------------------------------------------------------------ C15 monthly waveform

def test_monthly_waveform_shows_every_month_a_missing_month_is_null_not_zero():
    """prereg §3 (A′ = A plus Taraṅga's monthly waveform): all months of the span, gaps honest (§N.7.6)."""
    pair = {"start": "1990-03-15", "boundary": "1994-07-01", "end": "1996-02-10"}
    stored = [{"month": "1990-03-01", "integral": 0.25}, {"month": "1990-04-01", "integral": 0.5}]
    stored += [{"month": f"1994-{m:02d}-01", "integral": 1.0 + m} for m in range(1, 13)]
    rows = {r[0]: r for r in core.build_unit_data(pair, dict(sources(), taranga=stored))["MONTHLY_WAVEFORM"]}
    assert sorted(rows) == [1990, 1991, 1992, 1993, 1994, 1995, 1996]
    assert rows[1990][1] == "preceding" and rows[1990][2:4] == ("-", "-")          # Jan/Feb before the span
    assert rows[1990][4:6] == (0.25, 0.5) and set(rows[1990][6:]) == {"null"}      # no stored month => null
    assert rows[1994][1] == "both" and rows[1994][2:] == tuple(1.0 + m for m in range(1, 13))
    assert rows[1996][1] == "this" and rows[1996][2:4] == ("null", "null") and set(rows[1996][4:]) == {"-"}
