"""VC-1 declaration oracles, run by the existing mandatory governance shards.

These check pre-registration integrity, not experimental success. No chart values,
arm outputs, outcome evidence, baseline receipt or checkpoint verdict are fixtures.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
VC = ROOT / "00_ARCHITECTURE/briefs/l3_families/value_checkpoint"
DOC = "KSHETRA_ABLATION_PREREGISTRATION_v1_1.md"
SOURCE = ROOT / "00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_ABLATION_PREREGISTRATION_v1_0.md"


def declaration():
    return json.loads((VC / "preregistration.json").read_text())


def test_amended_copy_and_seal_preserve_the_original():
    text = (VC / DOC).read_text()
    d = declaration()
    seal = json.loads((VC / "DECLARATION_SEAL.json").read_text())
    assert 'version: "1.1"' in text
    assert "NR-KALA-R12-20261006" in text
    assert d["schema"] == "ky.vc1_preregistration/1"
    assert seal["source_sha256"] == hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    assert seal["source_sha256"] == "acfef33250518af78c2f05f8e4ff2a477b22e26e8ce1126bd485456a114bc019"
    assert set(seal["files"]) == {DOC, "preregistration.json"}
    for name, expected in seal["files"].items():
        assert hashlib.sha256((VC / name).read_bytes()).hexdigest() == expected, name


def test_missing_upstream_is_honest_and_cannot_authorize_execution():
    d = declaration()
    assert d["status"] == "PREBUILD_AWAITING_G1_FREEZE"
    assert d["baseline"]["head_sha"] is None
    assert d["baseline"]["code_digest"] is None
    assert d["freeze"]["preregistration_commit"] is None
    assert d["freeze"]["tracker_record"] is None
    assert d["execution_authorized"] is False
    assert d["baseline"]["required_repairs"] == list("abcdefg")
    assert d["baseline"]["receipt_path"] == "/Users/Dev/kalayantra/run/G1_BASELINE.json"
    assert d["baseline"]["model"] == "G1"
    assert d["baseline"]["replacement_or_compaction_admitted"] is False


def test_freeze_order_and_immutability_are_explicit():
    d = declaration()
    assert d["freeze"]["order"] == [
        "full_G1_independently_accepted_and_frozen",
        "bind_G1_head_and_code_digest_to_preregistration_commit_and_content_hashes",
        "record_binding_in_tracker",
        "VC-2_READY",
        "generate_all_arm_outputs",
        "both_independent_judges_score",
        "adjudicate_and_record_D-VC",
    ]
    assert d["freeze"]["after_edit"] == "new_item_new_version_new_freeze_before_new_outputs"
    assert d["freeze"]["preexisting_outputs"] == "invalidate_run"
    assert d["freeze"]["binding_required_before_ready"] == [
        "G1_head_sha", "G1_code_digest", "preregistration_commit", "declaration_sha256",
        "protocol_sha256", "baseline_receipt_sha256", "tracker_event_ref",
    ]


def test_three_arms_and_matched_budgets():
    d = declaration()
    assert [(a["id"], a["adds"]) for a in d["arms"]] == [
        ("A", ["sangam_windows"]),
        ("A_prime", ["sangam_windows", "taranga_monthly_waveform"]),
        ("B", ["sangam_windows", "taranga_monthly_waveform", "G1_segments_and_term_composition"]),
    ]
    assert d["presentation"] == {
        "same_source_snapshot": True, "same_shared_information": True,
        "same_renderer_and_layout": True, "max_words_per_arm_pair": 1200,
        "budget_overflow": "not_evaluable_no_silent_truncation",
        "labels": ["P", "Q", "R"], "partial_blinding_disclosed": True,
        "seed": "first_8_hex_digits_of_protocol_sha256",
        "map_reveal": "after_both_judges_return",
        "outcomes_visible_to_judges": False,
    }


def test_real_population_and_ordinary_control_are_required():
    p = declaration()["population"]
    assert p["chart_scope"] == ["482012f1-710e-4a25-994a-93821f5871aa"]
    assert p["requires"] == ["consent", "real_outcome_records", "evaluation_eligible"]
    assert p["synthetic_in_denominator"] is False
    assert p["class_scope"] == "six_calibrated_classes_from_frozen_G1_receipt"
    assert p["pairs"] == "adjacent_MD_both_chapters_inside_LEL_covered_span"
    assert p["max_pairs_per_chart"] == 8
    assert p["selection"] == "ascending_sha256(chart_id|pair_index)_then_pair_index"
    assert p["ordinary"] == {
        "criterion": "LEL_event_count_at_or_below_nearest_rank_25th_percentile",
        "selection": "lowest_hash_qualifier_reserve_before_filling_other_slots",
        "required_scored_pairs": 1, "if_absent": "insufficient_evidence",
    }
    assert p["minimum_scored_pairs"] == 2
    assert p["selection_before_outputs"] is True


def test_rubric_and_independence_are_preserved():
    d = declaration()
    r = d["rubric"]
    assert r["dimensions"] == ["participants", "conditions", "clocks", "relationships", "uncertainty"]
    assert r["dimension_scores"] == {"0": "absent", "1": "change_named", "2": "specific_moved_operand_identified"}
    assert r["driver"] == "classical_operand_drove_change_not_just_witness_presence"
    assert r["recurrence"] == "matched_mechanism_identity_not_narrative_template"
    assert r["binary_items"] == ["driver", "recurrence"]
    assert d["judges"] == {
        "primary": "fresh_context_review_agent", "secondary": "Kimi_K3_effort_max",
        "different_tools": True, "author_scores": False, "author_adjudicates": False,
        "author_sees_outputs": "after_both_judges_return",
        "inputs": ["sealed_rubric", "blinded_outputs"],
        "disagreement_or_cannot_tell": "native_adjudication",
        "ambiguous": "censored_not_scored",
        "dimension_or_recurrence_disagreement": "native_adjudication",
    }
    assert "recurrence with changes in participants, conditions, clocks, relationships and uncertainty" in r["distinction_text"]


def test_censoring_ceiling_and_conjunctive_four_way_verdicts():
    d = declaration()
    assert d["censoring"] == {
        "stratum": ["chart_id", "event_class"], "also_report_per_chart": True,
        "numerator": "native_adjudicated_ambiguous_pairs",
        "denominator": "all_selected_eligible_pairs_before_censoring",
        "excluded_from_all_scores": True, "ceiling": {"numerator": 1, "denominator": 5},
        "block_when": "censored_times_5_greater_than_selected",
        "zero_selected": "insufficient_evidence", "above_ceiling": "insufficient_evidence",
        "pooled_rescue": False,
        "chart_aggregation": chart_aggregation_contract(),
    }
    assert d["verdicts"]["allowed"] == ["pass", "fail", "insufficient_evidence", "not_evaluable"]
    assert d["verdicts"]["precedence"] == ["not_evaluable", "insufficient_evidence", "fail", "pass"]
    assert d["verdicts"]["pass_all"] == [
        "B_driver_exceeds_A_prime_on_strict_majority_and_never_below",
        "B_dimension_2_where_A_prime_at_most_1_on_scored_ordinary_control",
        "B_recurrence_1_on_at_least_half_scored_pairs",
    ]
    assert d["verdicts"]["partial_pass"] == "fail"
    assert d["verdicts"]["nonapproval"] == "park_G2_preserve_G1"
    assert d["verdicts"]["automatic_production_flip"] is False
    assert d["verdicts"]["report_per_arm"] is True
    assert d["evidence"]["actual_scores"] is None
    assert d["evidence"]["actual_verdict"] is None


def chart_aggregation_contract():
    return {
        "pair_identity": ["chart_id", "pair_index"],
        "denominator": "unique_selected_eligible_pairs_across_classes_before_censoring",
        "numerator": "unique_pairs_native_adjudicated_ambiguous_in_any_class",
        "mixed_class_ambiguity": "count_once_for_chart_keep_scoring_exclusions_stratum_local",
    }


@pytest.mark.parametrize("ambiguous_cells,expected_ambiguous,blocked", [
    ({(0, 0), (1, 1)}, 2, True),  # 2/5 blocks; pooling gives 2/30 and would pass.
    ({(0, 0), (1, 0)}, 1, False),  # The same pair in two classes counts once.
    ({(c, 0) for c in range(6)}, 1, False),  # Exactly 20% remains admissible.
    (set(), 0, False),
])
def test_chart_censoring_deduplicates_pairs_and_unions_class_ambiguity(
    ambiguous_cells, expected_ambiguous, blocked,
):
    # Declaration oracle only: no scorer or checkpoint result is implemented here.
    # Removing the rule, pooling class observations, or requiring all classes to
    # agree must fail. Both sealed declarations must carry the same contract.
    d = declaration()
    rule = d["censoring"].get("chart_aggregation")
    assert rule == chart_aggregation_contract(), "chart aggregation must be explicit"
    text = (VC / DOC).read_text()
    assert "```json\n" in text, "human-readable chart aggregation must be explicit"
    human_rule = json.loads(text.split("```json\n", 1)[1].split("\n```", 1)[0])
    assert human_rule == {"chart_aggregation": rule}

    # Five selected chapter pairs repeated over six synthetic classes; duplicate
    # judge/arm rows cannot inflate either count. These are arithmetic fixtures.
    rows = [
        {"chart_id": "chart-example", "pair_index": pair, "event_class": cls,
         "ambiguous": (cls, pair) in ambiguous_cells}
        for cls in range(6) for pair in range(5)
    ]
    identity = lambda row: tuple(row[key] for key in rule["pair_identity"])
    selected = {identity(row) for row in rows + rows}
    ambiguous = {identity(row) for row in rows + rows if row["ambiguous"]}
    assert len(selected) == 5
    assert len(ambiguous) == expected_ambiguous
    ceiling = d["censoring"]["ceiling"]
    assert (len(ambiguous) * ceiling["denominator"] >
            len(selected) * ceiling["numerator"]) is blocked
    # Each stratum is at most 1/5 even when the chart ceiling blocks 2/5.
    assert all(sum(row["ambiguous"] for row in rows if row["event_class"] == cls) <= 1
               for cls in range(6))
    if blocked:
        assert sum(row["ambiguous"] for row in rows) == 2
        assert len(rows) == 30
        assert 5 * sum(row["ambiguous"] for row in rows) <= len(rows)


@pytest.mark.parametrize("section", [
    "§1 — Purpose and limits", "§2 — Baseline and freeze protocol",
    "§3 — Population, pairs and arms", "§4 — Independent scoring",
    "§5 — Verdicts and censoring", "§6 — Evidence and handoff",
    "§7 — Interpretations and source anchors",
])
def test_human_readable_protocol_is_complete(section):
    text = (VC / DOC).read_text()
    assert section in text
    assert "(I) INTERPRETATION" in text
    assert "No experimental result is claimed" in text


def test_suite_is_in_existing_mandatory_ci_without_dropping_any_paths():
    # Existing discovery is the wiring; no new workflow or tracker behaviour.
    import ci_shard
    me = Path(__file__).resolve()
    shards = ci_shard.partition(ci_shard.test_files(), 5)
    assert sum(me in s for s in shards) == 1
    assert ci_shard.verify(ci_shard.test_files(), shards) == []
    ci = (ROOT / ".github/workflows/ci.yml").read_text()
    assert 'python -m pytest "${FILES[@]}"' in ci
    # K9-23 adds the required Kāla DB gate; preserve VC-1's dependencies (including main's J5S rehearsal)
    # while allowing the aggregate to require additional proof.
    needs = yaml.safe_load(ci)["jobs"]["governance-tool-tests"]["needs"]
    assert {"changes", "governance-tool-tests-shard", "governance-readback-tests", "gochara-j5s-full-class-seal"} <= set(needs)


def test_seal_generator_is_deterministic_and_check_rejects_tampering(tmp_path):
    # Exercise the real generator in an isolated miniature tree; no git/DB/cloud.
    root = tmp_path / "tree"
    target = root / VC.relative_to(ROOT)
    shutil.copytree(VC, target)
    original = root / SOURCE.relative_to(ROOT)
    original.parent.mkdir(parents=True)
    shutil.copy2(SOURCE, original)
    script = target / "seal_declaration.py"
    before = (target / "DECLARATION_SEAL.json").read_bytes()
    run = lambda *args: subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)
    assert run("--write").returncode == 0
    assert (target / "DECLARATION_SEAL.json").read_bytes() == before
    assert run("--check").returncode == 0
    with (target / DOC).open("a") as out:
        out.write("\nSilent post-freeze amendment\n")
    bad = run("--check")
    assert bad.returncode != 0 and "seal mismatch" in bad.stderr
    assert (target / "DECLARATION_SEAL.json").read_bytes() == before
