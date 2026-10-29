"""Rule Book engine (E3a) — compare the evaluator with an independently authored oracle file.

The oracle file (``rulebook-oracle-v1``) is written by someone other than the evaluator's
author, from the cards and the fixtures, by explicit arithmetic. This module only runs
the evaluator on the same fixtures and lists every difference. It never edits an
expectation.

Part A cases carry an inline synthetic card (compiled here with the E1 compiler).
Part B cases name a rule id; the rule is taken from the private bundle/manifest.
Each case day is evaluated on its own one-day grid: states depend only on that day's
sunrise instant, so this is exact, and it needs no sunrise for days the oracle did not use.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Mapping, Optional

from ..compiler import compile_card
from . import constants as K
from .chart import chart_from_fixture
from .dayatom import TableSunrise, build_grid
from .driver import prepare_chart
from .evaluator import combine_member_cards, evaluate_plan
from .irtree import operand_table
from .plan import CardPlan, Unsupported, plan_card
from .resolve import EvalContext
from .sky import sky_from_fixture

EXCLUDED = "EXCLUDED"
UNSUPPORTED = "UNSUPPORTED"


def plans_for_inline_card(card: Mapping[str, Any]) -> List[CardPlan]:
    res = compile_card(card)
    if res.status != "active" or res.ir is None:
        raise Unsupported("CARD_NOT_ACTIVE", f"{card.get('card_id')}: {res.reasons}")
    return [plan_card(res.ir, operand_table(card))]


def plans_for_rule(rule_id: str, manifest: Mapping[str, Any], bundle: Mapping[str, Any]) -> Optional[List[CardPlan]]:
    """Plans of a bundle rule; None when the manifest says the rule is node-excluded."""
    status = None
    for u in manifest["units"]:
        for m in u["members"]:
            if m["rulebook_id"] == rule_id:
                status = m["status"]
    if status == "excluded_node":
        return None
    if status != "evaluable":
        raise Unsupported("RULE_NOT_EVALUABLE", f"{rule_id}: manifest status {status}")
    return [plan_card(c["ir"], c["operands"]) for c in bundle["rules"][rule_id]["cards"]]


def evaluate_case(case: Mapping[str, Any], fixture: Mapping[str, Any], plans: Optional[List[CardPlan]]) -> Dict[str, str]:
    if plans is None or any(p.excluded_node for p in plans):
        return {"": EXCLUDED}
    chart = chart_from_fixture(fixture["chart"])
    sky = sky_from_fixture(fixture["sky"])
    provider = TableSunrise(fixture["sunrise"])
    out: Dict[str, str] = {}
    for day in sorted((case.get("days") or {})):
        d = date.fromisoformat(day)
        prepare_chart(chart, d, d)
        grid = build_grid(d, d, provider)
        ctx = EvalContext(chart, sky, grid)
        state = combine_member_cards([evaluate_plan(p, ctx) for p in plans])
        out[day] = K.STATE_CODE[state.at(0).value]
    return out


def run(doc: Mapping[str, Any], *, manifest: Optional[Mapping[str, Any]] = None, bundle: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    if doc.get("oracle_schema") != "rulebook-oracle-v1":
        raise ValueError("not a rulebook-oracle-v1 file")
    mismatches: List[Dict[str, Any]] = []
    n_cases = n_days = 0
    for case in doc["cases"]:
        n_cases += 1
        fixture = doc["fixtures"][case["fixture"]]
        if "card" in case:
            try:
                plans: Optional[List[CardPlan]] = plans_for_inline_card(case["card"])
            except Unsupported as exc:
                plans = None
                if case.get("expect") != "EXCLUDED":
                    mismatches.append({"case": case["case_id"], "day": None, "expected": case.get("expect") or "values", "got": f"{UNSUPPORTED}:{exc.code}"})
                    continue
        else:
            if manifest is None or bundle is None:
                raise ValueError("part B needs the manifest and bundle")
            plans = plans_for_rule(case["rule_id"], manifest, bundle)
        if case.get("expect") == "EXCLUDED":
            got = evaluate_case(case, fixture, plans)
            if got != {"": EXCLUDED}:
                mismatches.append({"case": case["case_id"], "day": None, "expected": EXCLUDED, "got": "evaluated"})
            n_days += 1
            continue
        got = evaluate_case(case, fixture, plans)
        for day, want in sorted(case["days"].items()):
            n_days += 1
            have = got.get(day)
            if have != want:
                mismatches.append({"case": case["case_id"], "rule": case.get("rule_id"), "day": day, "expected": want, "got": have})
    return {"cases": n_cases, "values": n_days, "mismatches": mismatches}
