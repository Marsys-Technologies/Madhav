"""D-OWNER-TESTS-20261016 §Authoritative standard; CLAUDE.md §N.8.

Guard the campaign's per-claim review contract against the superseded blanket rule.
"""
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[4]
CAMPAIGN = ROOT / "00_ARCHITECTURE/briefs/kalayantra"
DECISION = "D-OWNER-TESTS-20261016"


def _objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def test_step_review_measures_require_claims_instead_of_every_reversion():
    model = json.loads((ROOT / "00_ARCHITECTURE/control/kalayantra/plan_model.json").read_text())
    measures = [
        node["measures"].lower()
        for item in _objects(model) if "step_evidence" in item
        for node in _objects(item["step_evidence"])
        if "measures" in node and re.search(r"\breview(?:er)?\b", node["measures"], re.I)
    ]
    required = (
        "pinned merged head", "reviewer, not the author", "every distinct production claim",
        "brief, packet and cited classical rules", "in the verdict",
        "each claim has at least one doctrine-grounded oracle", "classical source cited; b.3/b.10",
        "single planted reversion failed at that head", "every real defect was fixed with fail-on-revert",
        DECISION.lower(),
    )
    invalid = [text for text in measures if "every reversion" in text or not all(term in text for term in required)]
    assert measures and not invalid, invalid


def test_testing_standard_decision_is_active_and_preserves_the_owner_standard():
    text = (CAMPAIGN / "DECISION_TESTING_STANDARD_v1_0.md").read_text()
    frontmatter = text.split("---", 2)[1]
    standard = text.split("## Authoritative standard (verbatim)\n", 1)[1].split("\n## ", 1)[0].lower()
    required = (
        DECISION.lower(), "authoritative and campaign-wide", "tests are optimum, not extraneous",
        "oracles pass at the pinned merged head", "the reviewer — not the author — enumerates every distinct production claim",
        "brief, packet and cited classical rules", "writes the list into the verdict",
        "each claim has at least one doctrine-grounded oracle (classical source cited; b.3/b.10)",
        "single planted reversion actually fails at that head", "every reversion that exposes a real defect is fixed",
        "known real defects are fixed regardless", "at most one reversion per claim; no combinatorial variants",
        "non_blocking and never blocks met", "never golden-capture current output",
        "never ask for an oracle per mutant", "one bounded review round",
        "non_blocking findings never trigger another round", "a second round only for a blocking finding",
        "n.8", "n.7.6 honest nulls", "sr-a4-01 strict ordered completion", "a1", "personal-data handling",
    )
    assert re.search(r"(?m)^status: ACTIVE$", frontmatter) and all(term in standard for term in required)


def test_amended_cards_and_prompts_do_not_require_an_oracle_per_mutant():
    paths = (
        "fleet/cards/KARAKA.md", "fleet/cards/PARIKSAKA.md", "fleet/cards/BOOTSTRAP_REVIEWER.md",
        "prompts/KARAKA.md", "prompts/PARIKSAKA.md",
    )
    forbidden = (
        "mutation survival fails", "a surviving mutation is a finding", "missing/live mutants",
        "each mutation the card names as a test", "each must fail on base and pass on head",
        "a mutation the card names that the pr does not carry is a finding", "name new mutants for the brief",
    )
    invalid = []
    for path in paths:
        text = (CAMPAIGN / path).read_text().lower()
        # Preserve explicit prohibitions of per-mutant demands, rather than banning the term itself.
        demands = re.sub(r"never (?:ask for|demand) an oracle per mutant", "", text)
        if (DECISION.lower() not in text
                or not re.search(r"oracle/claim|per-claim|one/claim|per distinct production claim", text)
                or any(term in demands for term in (*forbidden, "oracle per mutant", "every reversion"))):
            invalid.append(path)
    assert not invalid, invalid
