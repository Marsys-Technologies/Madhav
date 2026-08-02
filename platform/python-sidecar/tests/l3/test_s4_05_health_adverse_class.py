"""
S4-05 regression suite — the health/adverse event class in the gochara sweep grammar.

ṢAḌ-DARŚANA registry item 9 (`SHAD_DARSHANA_BRIEF_v2_0.md` §1 row 9), closing
**DP-4** (`KALA_TRANSFORMATION_HANDOFF_v1_0.md` §II.3: *"gochara sweep has no
health/adverse event class — the data root of the only trust-breaking veto
class"*).

────────────────────────────────────────────────────────────────────────────
THE SCENARIO THIS SUITE RE-TESTS (verbatim provenance, not reconstructed)
────────────────────────────────────────────────────────────────────────────
`UAT_BATTERY_v1_0.md` §S4-05 defines the query:

    "Is there a rough patch coming for my health in the near future?
     I'd rather know than not know."

`UAT_DARPANA_REPORT_v1_0.md` §2 records what the instrument answered, and why
it was the campaign's single TRUST-BREAKING veto:

    "I ran the forward hazard-scan on your transits ... and on the health side
     it comes back clean — no adverse window flagged across roughly the next
     three years."

and the adversarial audit's first confirmation, which is precisely what this
suite guards:

    "The gochara 'hazard-scan' is structurally incapable of flagging health.
     The entire `kala_gochara_windows` table (all charts) models only the event
     classes `career_advancement`, `major_gain`, `marriage`. There is **no
     health event class** ... 'Clean on the health side' therefore reports a
     null capability as an affirmative clearance."

The failure is therefore NOT a bad astrological judgment — it is a GRAMMAR
gap: the sweep's event-class universe contained no class whose
`brahma_event_ontology.domain` is `health`, and (a second, wider face of the
same gap) no adverse-valence class of ANY domain, so
`gochara_election_avoidance_get`'s `is_adverse = true` surface was
structurally empty for every chart ever built.

Each test below fails on the pre-item-9 tree and states, in its own docstring,
which limb of that audit it re-tests.

DISCIPLINE NOTES
  * These assertions read the ONE canonical domain vocabulary
    (`brahma_event_ontology`, migrations 388 + 456) via
    `services.gochara_grammar.event_class_scope`. No test here invents an
    event-class name or a domain name — a new taxonomy would itself violate
    the campaign's ONE-VOCABULARY rail (brief §7).
  * `kala_gochara_windows` DATA is untouchable (brief §7). Nothing here
    mutates or asserts against existing rows for the three legacy classes;
    the extension is purely additive.
"""
from pathlib import Path

import pytest

import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.gochara_grammar.event_class_scope import (  # noqa: E402
    DOMAIN_MAP,
    HEALTH_ADVERSE_EVENT_CLASSES,
    SWEEP_EVENT_CLASSES,
    sweep_domains,
)
from services.gochara_intensity.valence import VALENCE_MAP, is_adverse  # noqa: E402
from services.gochara_intensity.engine import SHAPE_MAP  # noqa: E402
from services.ka_gochara_resonance.writer import (  # noqa: E402
    TARGET_EVENT_CLASSES,
    build_resonance_rows,
)

MIGRATION_388 = (
    Path(__file__).parent.parent.parent.parent
    / "supabase/migrations/388_brahma_ghatana_ontology.sql"
)

# The 13-value canonical domain universe = `brahma_event_ontology.domain`'s own
# CHECK constraint (migration 388). `computeGocharaCoverage`'s
# `domains_not_covered` is exactly this universe minus the swept set, so this is
# the same arithmetic the served surface does.
CANONICAL_DOMAIN_UNIVERSE = frozenset(DOMAIN_MAP.values())


# ══════════════════════════════════════════════════════════════════════════
# 1. The veto itself — the sweep grammar could not see health at all
# ══════════════════════════════════════════════════════════════════════════


def test_s4_05_sweep_grammar_covers_the_health_domain():
    """Re-tests audit confirmation #1: *"There is no health event class."*

    RED on the pre-item-9 tree: the sweep's event-class universe was
    exactly {career_advancement (career), major_gain (wealth), marriage
    (relationship)} — `health` was absent, so every "is a rough patch coming
    for my health" question was answered from a scan that could never see
    health, and its silence was read as an all-clear.
    """
    assert "health" in sweep_domains(), (
        "S4-05 REGRESSION: the gochara sweep's event-class universe covers no "
        f"health-domain class (covered domains: {sorted(sweep_domains())}). A "
        "health query answered from this sweep can only ever come back empty, "
        "and an empty answer WILL be read as an all-clear."
    )


def test_s4_05_health_classes_are_actually_in_the_sweep_scope():
    """Every canonical health-domain class is swept, not just one token class.

    Partial health coverage would be its own quiet misrepresentation: a
    "nothing on the health side" answer derived from `surgery` targets alone
    is not a health scan. The ontology's health domain is exactly
    {illness_acute, chronic_onset, surgery}; the sweep covers all three.
    """
    ontology_health_classes = {ec for ec, dom in DOMAIN_MAP.items() if dom == "health"}
    assert ontology_health_classes == set(HEALTH_ADVERSE_EVENT_CLASSES), (
        "the item-9 health scope must equal the canonical ontology's health "
        f"domain, not a hand-picked subset: ontology={sorted(ontology_health_classes)} "
        f"scope={sorted(HEALTH_ADVERSE_EVENT_CLASSES)}"
    )
    missing = ontology_health_classes - set(SWEEP_EVENT_CLASSES)
    assert not missing, f"health classes declared but not swept: {sorted(missing)}"


def test_s4_05_sweep_grammar_has_at_least_one_adverse_valence_class():
    """Re-tests the WIDER face of DP-4: before item 9 the sweep contained
    **zero** adverse-valence classes of any domain (career_advancement=gain,
    major_gain=gain, marriage=neutral), so `gochara_election_avoidance_get`'s
    `is_adverse = true` surface was structurally empty for every chart — not
    just for health.
    """
    adverse = [ec for ec in SWEEP_EVENT_CLASSES if is_adverse(None, ec)[0]]
    assert adverse, (
        "S4-05 REGRESSION: no swept event class carries an adverse valence, so "
        "the adverse-window surface (is_adverse = true) is empty by "
        "construction and any 'no adverse window' answer is vacuous."
    )
    # And the health classes specifically must be among them — a health scan
    # that can only report gains is not a hazard scan.
    adverse_health = [ec for ec in HEALTH_ADVERSE_EVENT_CLASSES if is_adverse(None, ec)[0]]
    assert adverse_health, "no health class resolves to an adverse valence"


def test_s4_05_domains_not_covered_no_longer_contains_health():
    """Mirrors, in Python, the exact derivation the served surface performs.

    `computeGocharaCoverage` (platform-mcp/src/tools/retrieval/
    register_gochara_windows.ts) computes
    `domains_not_covered = DISTINCT brahma_event_ontology.domain MINUS the
    domains of the classes this chart's sweep covered`, and
    `notCoveredFor(domain, coverage)` turns a hit in that list into a refusal.
    Health being in that list was the machine-readable form of the S4-05
    incapacity.
    """
    domains_not_covered = CANONICAL_DOMAIN_UNIVERSE - sweep_domains()
    assert "health" not in domains_not_covered, (
        "S4-05 REGRESSION: 'health' is still in the sweep's structurally-dark "
        f"domain set {sorted(domains_not_covered)}"
    )


# ══════════════════════════════════════════════════════════════════════════
# 2. ONE canonical vocabulary — no parallel taxonomy (brief §7 rail)
# ══════════════════════════════════════════════════════════════════════════


def test_no_parallel_taxonomy_every_swept_class_is_canonical():
    """Each swept class must be a real `brahma_event_ontology` event_class_id,
    present in every canonical mirror of that table (domain, valence, temporal
    shape). Inventing a new class name (e.g. "health_adverse") to close DP-4
    would violate the ONE-VOCABULARY rail and orphan the class from valence,
    shape, base-rate, and citation data."""
    for ec in SWEEP_EVENT_CLASSES:
        assert ec in DOMAIN_MAP, f"{ec} is not a canonical brahma_event_ontology class"
        assert ec in VALENCE_MAP, f"{ec} has no canonical valence"
        assert ec in SHAPE_MAP, f"{ec} has no canonical temporal shape"


def test_domain_map_is_the_full_27_class_ontology():
    """The domain mirror must stay diff-locked to the same 27-class ontology
    the sibling valence/shape mirrors track (`test_gochara_intensity.py`
    asserts 27 for both) — so a future ontology migration that adds a class
    trips CI here rather than silently shrinking the coverage universe."""
    assert len(DOMAIN_MAP) == 27
    assert set(DOMAIN_MAP) == set(VALENCE_MAP) == set(SHAPE_MAP)


def test_sweep_scope_is_the_resonance_writer_scope():
    """The resonance writer (which populates `gochara_resonance_map`, the table
    the sweep discovers its event classes from, and the table the served
    `coverage.event_classes_covered` is derived from) must read its scope from
    the shared constant — not keep a second, drifting copy."""
    assert tuple(TARGET_EVENT_CLASSES) == tuple(SWEEP_EVENT_CLASSES)


def test_legacy_classes_are_retained_additively():
    """`kala_gochara_windows` data is untouchable (brief §7): item 9 EXTENDS
    the grammar, it never narrows it. The three pre-existing classes must
    still be swept."""
    for ec in ("career_advancement", "major_gain", "marriage"):
        assert ec in SWEEP_EVENT_CLASSES


# ══════════════════════════════════════════════════════════════════════════
# 3. LAW ZERO — the health classes are grounded, not plausible-sounding
# ══════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("event_class", ["illness_acute", "chronic_onset", "surgery"])
def test_health_classes_are_seeded_with_real_classical_citations(event_class):
    """No fabrication: each health class must exist in the ontology seed with a
    real, non-empty `citations` array. The sweep's health rows inherit those
    citations through `build_resonance_rows(ontology_citation=...)`, so a class
    seeded without a citation would produce uncited "health" claims."""
    sql = MIGRATION_388.read_text()
    assert f"('{event_class}'," in sql, f"{event_class} not seeded in migration 388"
    block = sql.split(f"('{event_class}',", 1)[1].split("'1.0')", 1)[0]
    assert "ARRAY['BPHS" in block, (
        f"{event_class} carries no BPHS-rooted citation in its ontology seed — "
        "a health determination built on it would be uncited"
    )
    assert "'health'" in block, f"{event_class} is not seeded in the health domain"


def test_health_resonance_rows_carry_the_ontology_citation():
    """The bhava/lord/karaka rows the resonance writer builds for a health class
    must carry the ontology's own classical citation and be marked
    `uncited_extension=False`; the writer's own synthetic linkages stay
    `uncited_extension=True` with a NULL citation. Neither is ever dressed up
    as the other (B.10)."""
    # illness_acute's REAL signature_model + citations, migration 388.
    rows = build_resonance_rows(
        "illness_acute",
        houses=["6", "8"],
        lords=["6L", "8L"],
        karakas=["Mars", "Saturn"],
        ontology_citation="BPHS ch.6 (roga-bhava); Phaladeepika ch.6",
        sensitive_fact_rows=[{"fact_id": "f-health-1"}],
    )
    cited = [r for r in rows if r["target_type"] in ("bhava", "lord", "karaka")]
    assert cited, "no cited resonance rows built for illness_acute"
    for r in cited:
        assert r["classical_citation"] == "BPHS ch.6 (roga-bhava); Phaladeepika ch.6"
        assert r["uncited_extension"] is False

    extensions = [r for r in rows if r["target_type"] == "sensitive_degree"]
    assert extensions, "expected the writer's own synthetic linkage rows"
    for r in extensions:
        assert r["classical_citation"] is None
        assert r["uncited_extension"] is True


def test_health_classes_resolve_a_nonempty_signature_target_set():
    """Honest-empty is the correct behaviour for an ungrounded class — but a
    health class whose target set is ALWAYS empty would re-create S4-05 with
    extra steps (coverage claims health, sweep can never fire). Each health
    class must resolve real houses/lords/karakas from its ontology signature."""
    signatures = {
        "illness_acute": (["6", "8"], ["6L", "8L"], ["Mars", "Saturn"]),
        "chronic_onset": (["6", "8"], ["6L", "8L"], ["Saturn"]),
        "surgery": (["6", "8"], ["6L", "8L"], ["Mars"]),
    }
    for ec, (houses, lords, karakas) in signatures.items():
        rows = build_resonance_rows(
            ec, houses=houses, lords=lords, karakas=karakas,
            ontology_citation="BPHS ch.6 (roga-bhava)",
        )
        assert len(rows) >= len(houses) + len(lords) + len(karakas), (
            f"{ec} resolved too few resonance targets: {rows}"
        )
