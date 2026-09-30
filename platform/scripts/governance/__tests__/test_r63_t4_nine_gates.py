"""test_r63_t4_nine_gates.py — R63 (NIKASHA_CHANGE_REGISTER_v2_0.md).

T4 (`ASSET_ELEVATION_TEMPLATE_v2_0.md`, tier 4, unsealed) said "the eight gates" in 4 places while
its own §4 gate table already lists nine (Build added by ruling 17, decision 17). This test fails
against the pre-fix text (4 occurrences of the stale phrase) and passes once every occurrence reads
"the nine gates" instead. Does not touch T3 (`LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`,
sealed) — that document's own §5.2 text already says "nine in total" (line ~519), so T4's citation
of it is being corrected to match, not altered in substance.
"""
from __future__ import annotations

import pathlib

T4 = pathlib.Path(__file__).resolve().parents[4] / "00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md"


def test_t4_has_no_stale_eight_gates_phrase():
    text = T4.read_text(encoding="utf-8")
    assert "the eight gates" not in text, (
        "T4 still says 'the eight gates' somewhere — its own §4 table lists nine (R63)"
    )


def test_t4_nine_gates_phrase_present_in_all_four_known_locations():
    text = T4.read_text(encoding="utf-8")
    assert text.count("the nine gates") == 4, (
        f"expected exactly 4 occurrences of 'the nine gates' (§4 heading, its inherits line, the "
        f"T3-citation comment, and the closing 'Adapting per layer' line), got {text.count('the nine gates')}"
    )


def test_t4_gate_table_actually_lists_nine_gate_rows():
    text = T4.read_text(encoding="utf-8")
    gate_names = ["**Ldgr**", "**Idem**", "**Earn**", "**Null**", "**Vocab**", "**Carr**",
                  "**Narr**", "**Dens**", "**Build**"]
    for g in gate_names:
        assert g in text, f"gate table missing {g} — the nine-gate claim would be false"
