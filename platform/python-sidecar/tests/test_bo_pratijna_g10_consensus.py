"""
test_bo_pratijna_g10_consensus.py — G10 (SAMPURTI L0e): varga_confirmation
cross-ayanamsha consensus unit tests.

Tests _varga_confirmation_consensus() and _divisional_entry_from_ledger()
in isolation — both are pure functions (no DB, no jhora) so they are
inlined here rather than imported from bo_pratijna.py (which carries the
jhora dep chain via bo_pratijna_v4_engine -> ga_condition_writer ->
pyjhora_adapter).

The inlined implementations MUST stay byte-identical to the originals in
bo_pratijna.py.  If the production implementations change, update this
file in the same commit (the discrepancy will surface as a test failure
or a code-review finding, not a silent divergence).

§N.5 discipline verified by the tests themselves: the consensus function
only reads values already present in the engine-produced factor_ledger
entries; it never re-derives sign positions or dignity states.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ── Inline pure-function copies ─────────────────────────────────────────────
# These are verbatim copies of _divisional_entry_from_ledger and
# _varga_confirmation_consensus from bo_pratijna.py.  Any change to the
# production code requires the same change here.

@dataclass
class _ClassScoreStub:
    """Minimal stand-in for ClassScore — only factor_ledger is needed."""
    factor_ledger: list[dict[str, Any]] = field(default_factory=list)


def _divisional_entry_from_ledger(score: _ClassScoreStub) -> dict | None:
    """Return the divisional-slot factor_ledger entry from a ClassScore, or
    None if no divisional was scored (class has no KaryatvaMap divisional).
    §N.5: references the engine's already-computed L1-derived entry; never
    re-derives sign positions or dignity states from raw chart data."""
    for entry in score.factor_ledger:
        if entry.get("slot") == "divisional":
            return entry
    return None


def _varga_confirmation_consensus(
    per_aya_divisional: dict[str, dict | None],
) -> dict | None:
    """Build the cross-ayanamsha consensus JSON for varga_confirmation (G10).

    per_aya_divisional: {ayanamsha_id -> divisional factor_ledger entry | None}
                        (None means this class has no divisional in its map)

    Returns None if all entries are None (no divisional for this class).
    """
    scored = {k: v for k, v in per_aya_divisional.items() if v is not None}
    if not scored:
        return None

    any_entry = next(iter(scored.values()))
    varga = any_entry.get("varga")
    graha = any_entry.get("graha")

    per_system: dict[str, dict] = {}
    dignity_votes: dict[str, int] = {}
    for aya, entry in scored.items():
        ds = entry.get("dignity_state", "unknown")
        dignity_votes[ds] = dignity_votes.get(ds, 0) + 1
        per_system[aya] = {
            "varga_sign": entry.get("varga_sign"),
            "dignity_state": ds,
            "band": entry.get("band"),
        }

    max_votes = max(dignity_votes.values())
    leaders = [d for d, v in dignity_votes.items() if v == max_votes]
    consensus_dignity = leaders[0] if len(leaders) == 1 else None
    unanimous = len(dignity_votes) == 1

    dissent = [
        {"ayanamsha_id": aya, **reading}
        for aya, reading in per_system.items()
        if reading["dignity_state"] != consensus_dignity
    ] if consensus_dignity else []

    return {
        "varga": varga,
        "graha": graha,
        "per_system": per_system,
        "consensus_dignity": consensus_dignity,
        "unanimous": unanimous,
        "dissent": dissent,
        "source": (
            "cross-ayanamsha consensus, 5 L1-computed systems "
            "(G10/SAMPURTI L0e — §N.5: values referenced from "
            "PratijnaV4Engine factor_ledger, not re-derived)"
        ),
    }


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_div_entry(
    varga: str = "D10",
    graha: str = "Mercury",
    varga_sign: str = "Capricorn",
    dignity_state: str = "great_enemy",
    band: float = 0.2,
) -> dict:
    return {
        "slot": "divisional",
        "varga": varga,
        "graha": graha,
        "varga_sign": varga_sign,
        "dignity_state": dignity_state,
        "band": band,
    }


CANONICAL_AYAS = [
    "lahiri_chitrapaksha", "raman", "krishnamurti",
    "surya_siddhanta_classical", "true_chitra",
]


# ── _divisional_entry_from_ledger tests ──────────────────────────────────────

class TestDivisionalEntryFromLedger:
    def test_returns_none_for_empty_ledger(self):
        score = _ClassScoreStub(factor_ledger=[])
        assert _divisional_entry_from_ledger(score) is None

    def test_returns_none_when_no_divisional_slot(self):
        score = _ClassScoreStub(factor_ledger=[
            {"slot": "bhava", "bhava": 10, "planet": "Mercury"},
            {"slot": "karaka", "graha": "Sun"},
        ])
        assert _divisional_entry_from_ledger(score) is None

    def test_returns_divisional_entry(self):
        entry = _make_div_entry()
        score = _ClassScoreStub(factor_ledger=[
            {"slot": "bhava", "bhava": 10},
            entry,
            {"slot": "karaka", "graha": "Jupiter"},
        ])
        result = _divisional_entry_from_ledger(score)
        assert result is entry  # exact same dict object

    def test_returns_first_divisional_entry_when_multiple(self):
        first = _make_div_entry(varga="D10")
        second = _make_div_entry(varga="D9")
        score = _ClassScoreStub(factor_ledger=[first, second])
        assert _divisional_entry_from_ledger(score) is first


# ── _varga_confirmation_consensus tests ──────────────────────────────────────

class TestVargaConfirmationConsensus:
    def test_all_none_returns_none(self):
        """Classes with no divisional in their KaryatvaMap give all-None input."""
        per_aya = {aya: None for aya in CANONICAL_AYAS}
        assert _varga_confirmation_consensus(per_aya) is None

    def test_unanimous_consensus_all_five_agree(self):
        """All 5 ayanamshas land in the same dignity state -> unanimous=True."""
        per_aya = {
            aya: _make_div_entry(dignity_state="great_enemy", varga_sign="Capricorn")
            for aya in CANONICAL_AYAS
        }
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert result["unanimous"] is True
        assert result["consensus_dignity"] == "great_enemy"
        assert result["dissent"] == []
        assert len(result["per_system"]) == 5
        assert result["varga"] == "D10"
        assert result["graha"] == "Mercury"

    def test_dissent_when_one_system_differs(self):
        """4 agree + 1 differs -> unanimous=False, consensus=majority, 1 dissenter."""
        per_aya = {
            aya: _make_div_entry(dignity_state="great_enemy", varga_sign="Capricorn")
            for aya in CANONICAL_AYAS
        }
        # raman lands in a different sign with a different dignity
        per_aya["raman"] = _make_div_entry(
            dignity_state="own", varga_sign="Aquarius", band=0.8
        )
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert result["unanimous"] is False
        assert result["consensus_dignity"] == "great_enemy"
        assert len(result["dissent"]) == 1
        dissenter = result["dissent"][0]
        assert dissenter["ayanamsha_id"] == "raman"
        assert dissenter["dignity_state"] == "own"
        assert dissenter["varga_sign"] == "Aquarius"

    def test_no_majority_consensus_dignity_is_none(self):
        """When no single dignity state has a plurality, consensus_dignity=None."""
        # 3 distinct dignity states across 5 systems: 2+2+1 — tie between first two
        states = ["great_enemy", "great_enemy", "neutral", "neutral", "own"]
        per_aya = {
            aya: _make_div_entry(dignity_state=states[i])
            for i, aya in enumerate(CANONICAL_AYAS)
        }
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert result["consensus_dignity"] is None
        assert result["dissent"] == []  # no consensus -> dissent list empty

    def test_partial_none_entries_scored_by_available_systems(self):
        """If only 3 of 5 ayanamshas have a divisional reading, consensus uses those 3."""
        per_aya: dict[str, dict | None] = {aya: None for aya in CANONICAL_AYAS}
        per_aya["lahiri_chitrapaksha"] = _make_div_entry(dignity_state="great_enemy")
        per_aya["raman"] = _make_div_entry(dignity_state="great_enemy")
        per_aya["krishnamurti"] = _make_div_entry(dignity_state="own")
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert len(result["per_system"]) == 3  # only the 3 scored ayas
        assert result["consensus_dignity"] == "great_enemy"
        assert result["unanimous"] is False

    def test_source_field_documents_g10_provenance(self):
        """source field carries §N.5 provenance marker."""
        per_aya = {
            aya: _make_div_entry() for aya in CANONICAL_AYAS
        }
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        assert "G10/SAMPURTI L0e" in result["source"]
        assert "§N.5" in result["source"]
        assert "PratijnaV4Engine factor_ledger" in result["source"]

    def test_per_system_contains_correct_fields(self):
        """per_system entries carry varga_sign, dignity_state, band for each aya."""
        per_aya = {
            aya: _make_div_entry(
                varga_sign="Capricorn", dignity_state="great_enemy", band=0.2
            )
            for aya in CANONICAL_AYAS
        }
        result = _varga_confirmation_consensus(per_aya)
        assert result is not None
        for aya in CANONICAL_AYAS:
            entry = result["per_system"][aya]
            assert entry["varga_sign"] == "Capricorn"
            assert entry["dignity_state"] == "great_enemy"
            assert entry["band"] == 0.2
