"""test_e6_dens_tier_guard.py: DENS-TIER-GUARD, REGISTRY_REVISION 23, declarations 1.13.0 (strategist ruling N-98 / Dens memo item 3; STRICTER-ONLY).

The old vocabulary `^(?:tier|\\w+_tier|verification_pass_status)$` let ANY `*_tier` column count as a verification / confidence tier, among them
`bg_remedies.cost_tier` (a price bucket): a Dens lift on bg_remedies could have been a false PASS. The vocabulary is now CLOSED (`ac.dens_tier_counts`, the one classifier):

  a column counts as a tier ONLY when
    (a) its name is exactly `tier` or `verification_pass_status`, or
    (b) the asset DECLARES it in `density_tier_columns: [{column, why, evidence}]` (validated; no asset declares one yet: inert), and
    (c) its name carries no deny-listed word (cost, price, pricing, plan, access, subscription, billing, fee, tariff: a whole `_`-word, case-insensitive):
        a deny-listed name never counts, even declared, and a declared one is REFUSED.
  `severity_tier`, `cost_tier`, `access_tier`, `signature_tier` ... count for nothing undeclared.

Offline (synthetic tree + stubbed layer) plus REAL_SQL tests that read the column list through the census's own `catalog()` from the disposable Postgres.
Every guard has a mutation test: switch the guard off and the verdict the guard exists to prevent appears.

Run:
  python -m pytest platform/scripts/governance/__tests__/test_e6_dens_tier_guard.py -v
"""
from __future__ import annotations

import inspect
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_1_dens_repair as dr  # noqa: E402
import test_e6_1_p1_registry_rollup as p1  # noqa: E402
import test_w2_1_earned_verdicts as w1  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

tree = dr.tree                                           # the synthetic-source-tree fixture (re-exported for pytest)
PASS, PARTIAL, FAIL, NO_DET = ac.PASS, ac.PARTIAL, ac.FAIL, ac.NO_DET
_REAL_CATALOG = ac.catalog                               # captured before any test stubs it
OLD_OPEN = re.compile(r"^(?:tier|\w+_tier|verification_pass_status)$", re.I)      # the regex this guard replaces (mutant / witness only)

WHY = "confidence tier of the served row: how well the claim is verified"
EVID = "platform/scripts/governance/__tests__/test_e6_dens_tier_guard.py:1"       # a real file that names every column the valid declarations below use
ENT = dict(column="confidence_tier", why=WHY, evidence=EVID)
DENIED_NAMES = ["cost_tier", "price_tier", "pricing_tier", "plan_tier", "access_tier", "subscription_tier", "billing_tier", "fee_tier", "tariff_tier",
                "tier_cost", "tier_price", "Cost_Tier", "ACCESS_TIER", "plan_cost_tier"]
# F2 (review of PR 3037): the deny-listed meaning in every other SPELLING: run together, camelCase, digits, plurals, split letters, a deny word led / trailed by anything
SPELLINGS = ["costtier", "CostTier", "costTier", "COSTTIER", "pricetier", "priceTier", "feetier", "accesstier", "costs_tier", "plans_tier", "prices_tier", "fees_tier", "cost1_tier",
             "cost_1_tier", "costbucket_tier", "c_o_s_t_tier", "tier_costs", "tiercost", "unitcost_tier", "AccessTier", "tariffTier", "subscriptionsTier", "pricingTier", "billing2tier"]


def _doc(entry_extra, aid="bg_x"):
    return dict(version="1.13.0", kind_enum=list(ac.DECLARED_KINDS), assets={aid: dict({"kind": "data"}, **entry_extra)})


def _bad(dt, match, e=None):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(dict(e or {}, density_tier_columns=dt)))


def _scan(tree, sql, cols, declared=None, contract=True, table="t_dens"):
    tree.write(tree.layers / "L0_x", "q.ts", dr._cap(sql, contract=contract))
    return dr._REAL_SCAN(tree.roots, [table, "bg_x"], shared=set(), columns={table: list(cols)}, outside_roots=(), tier_declared=declared)


def _v(cap):
    return ac._grade_dens(cap, "t_dens")


# ═════════════════════════ the one classifier ═════════════════════════

@pytest.mark.parametrize("name, declared, counts", [
    ("tier", (), True), ("TIER", (), True), ("verification_pass_status", (), True), ("Verification_Pass_Status", (), True),
    ("cost_tier", (), False), ("access_tier", (), False), ("price_tier", (), False), ("severity_tier", (), False),
    ("signature_tier", (), False), ("evidence_tier", (), False), ("confidence_tier", (), False), ("confidence", (), False),
    ("confidence_tier", ("confidence_tier",), True), ("Confidence_Tier", ("confidence_tier",), True), ("confidence_tier", ("CONFIDENCE_TIER",), True),
    ("severity_tier", ("confidence_tier",), False),                          # declaring one column does not open the others
    ("cost_tier", ("cost_tier",), False), ("access_tier", ("access_tier",), False),            # deny-listed: never, even declared
    ("planet_tier", ("planet_tier",), False), ("accessory_tier", ("accessory_tier",), False),  # fail-closed: a name that BEGINS with a deny word is denied (declare another name)
    ("feedback_tier", ("feedback_tier",), False), ("prices_tier", ("prices_tier",), False),    # F2: the plural is the deny word; it was pinned as counting before the review
    ("costtier", ("costtier",), False), ("CostTier", ("CostTier",), False), ("c_o_s_t_tier", ("c_o_s_t_tier",), False),
    ("evidence_grade_tier", ("evidence_grade_tier",), True), ("verified_tier", ("verified_tier",), True), ("soundness_tier", ("soundness_tier",), True),
    (None, ("tier",), False), (7, (), False),
])
def test_the_classifier_table(name, declared, counts):
    assert ac.dens_tier_counts(name, declared) is counts


@pytest.mark.parametrize("name", DENIED_NAMES)
def test_a_deny_listed_name_never_counts_declared_or_not(name):
    assert ac.dens_tier_denied_word(name) is not None
    assert not ac.dens_tier_counts(name) and not ac.dens_tier_counts(name, (name, name.lower(), name.upper()))


@pytest.mark.parametrize("name", SPELLINGS)
def test_F2_a_deny_listed_name_in_any_spelling_never_counts_and_is_refused_by_the_validator(name):
    assert ac.dens_tier_denied_word(name) is not None, name
    assert not ac.dens_tier_counts(name, (name, name.lower())), name
    _bad([dict(ENT, column=name)], "deny-listed word")


@pytest.mark.parametrize("name", ["tier", "verification_pass_status", "confidence_tier", "evidence_tier", "severity_tier", "quality_tier", "horizon_tier", "probability_tier",
                                  "intensity_tier", "signature_tier", "grade_tier", "certainty_tier", "reliability_tier", "evidence_grade_tier", "soundness_tier", "verified_tier",
                                  "confidenceTier", "VerificationTier"])
def test_F2_the_fail_closed_match_does_not_deny_a_real_verification_name(name):
    assert ac.dens_tier_denied_word(name) is None, name


def test_the_deny_list_and_the_exact_names_are_the_ruled_ones():
    assert ac.DENS_TIER_EXACT == {"tier", "verification_pass_status"}
    assert ac.DENS_TIER_DENY_WORDS == {"cost", "price", "pricing", "plan", "access", "subscription", "billing", "fee", "tariff"}
    assert not hasattr(ac, "DENS_TIER_COLUMN"), "the open regex is removed: ONE definition (dens_tier_counts)"


def test_the_old_open_regex_is_what_the_guard_closes():
    for n in ("cost_tier", "access_tier", "price_tier", "severity_tier", "signature_tier"):
        assert OLD_OPEN.match(n) and not ac.dens_tier_counts(n), n                       # the witness: counted before, counts for nothing now


# ═════════════════════════ the scan: closed list ═════════════════════════

@pytest.mark.parametrize("col", ["cost_tier", "access_tier", "price_tier", "severity_tier", "signature_tier", "plan_tier"])
def test_a_non_vocabulary_tier_column_is_not_a_tier_column_PARTIAL_never_PASS(tree, col):
    cap = _scan(tree, f"SELECT id, {col} FROM t_dens", ["id", col])
    d = _v(cap)
    assert d["v"] == PARTIAL and "no tier column in its served select" in d["measured"], (col, d)


@pytest.mark.parametrize("col", ["tier", "verification_pass_status"])
def test_the_two_literal_names_still_count(tree, col):
    d = _v(_scan(tree, f"SELECT id, {col} FROM t_dens", ["id", col]))
    assert d["v"] == PASS and col in d["measured"], d


def test_select_star_expands_only_to_the_closed_vocabulary(tree):
    cols = ["id", "cost_tier", "access_tier", "severity_tier"]
    assert _v(_scan(tree, "SELECT * FROM t_dens", cols))["v"] == PARTIAL
    assert ac._select_tier("*", None, "t_dens", cols) == (ac.TIER_NO, [])
    assert ac._select_tier("*", None, "t_dens", cols + ["tier"]) == (ac.TIER_YES, ["tier"])               # only `tier` of the star
    assert ac._select_tier("*", None, "t_dens", cols + ["confidence_tier"], ("confidence_tier",)) == (ac.TIER_YES, ["confidence_tier"])
    assert ac._select_tier("*", None, "t_dens", cols + ["cost_tier"], ("cost_tier",)) == (ac.TIER_NO, [])


def test_a_declared_confidence_tier_counts_only_for_the_declared_table(tree):
    sql, cols = "SELECT id, confidence_tier FROM t_dens", ["id", "confidence_tier"]
    assert _v(_scan(tree, sql, cols))["v"] == PARTIAL                                                      # undeclared: nothing
    d = _v(_scan(tree, sql, cols, declared={"t_dens": ["confidence_tier"]}))
    assert d["v"] == PASS and "confidence_tier" in d["measured"], d
    assert _v(_scan(tree, sql, cols, declared={"other_t": ["confidence_tier"]}))["v"] == PARTIAL           # declared for a different table: does not apply here
    assert _v(_scan(tree, sql, cols, declared={"t_dens": ["severity_tier"]}))["v"] == PARTIAL               # declaring another column opens nothing else


def test_a_declared_deny_listed_name_never_counts_even_if_the_validator_were_bypassed(tree):
    for col in ("cost_tier", "access_tier"):
        d = _v(_scan(tree, f"SELECT id, {col} FROM t_dens", ["id", col], declared={"t_dens": [col]}))
        assert d["v"] == PARTIAL, (col, d)                                                                  # defence in depth: the classifier denies it at the scan too


def test_a_qualified_declared_tier_column_follows_the_same_attribution_rules(tree):
    declared = {"t_dens": ["confidence_tier"]}
    cols = ["id", "confidence_tier"]
    assert _v(_scan(tree, "SELECT a.id, a.confidence_tier FROM t_dens a JOIN t_o b ON b.id = a.oid", cols, declared))["v"] == PASS
    assert _v(_scan(tree, "SELECT a.id, b.confidence_tier FROM t_dens a JOIN t_o b ON b.id = a.oid", cols, declared))["v"] == PARTIAL   # b's column is not ours
    assert _v(_scan(tree, "SELECT lower(confidence_tier) AS c FROM t_dens", cols, declared))["v"] == PARTIAL                              # an expression is no tier column


def test_a_tier_column_without_a_contract_is_not_surfaced_for_a_non_vocabulary_name(tree):
    d = _v(_scan(tree, "SELECT id, cost_tier FROM t_dens", ["id", "cost_tier"], contract=False))
    assert d["v"] == FAIL and "a tier column is selected without a contract" not in d["measured"], d
    d = _v(_scan(tree, "SELECT id, tier FROM t_dens", ["id", "tier"], contract=False))
    assert d["v"] == FAIL and "a tier column is selected without a contract" in d["measured"], d


# ═════════════════════════ mutation tests: switch each guard off and the false verdict appears ═════════════════════════

def test_MUTATION_the_old_open_regex_lifts_cost_tier_to_PASS(tree, monkeypatch):
    sql, cols = "SELECT id, cost_tier FROM t_dens", ["id", "cost_tier"]
    assert _v(_scan(tree, sql, cols))["v"] == PARTIAL                                                       # the guard
    monkeypatch.setattr(ac, "dens_tier_counts", lambda name, declared=(): bool(OLD_OPEN.match(name)))        # the mutant: the open vocabulary
    assert _v(_scan(tree, sql, cols))["v"] == PASS                                                          # the false lift the guard prevents


def test_MUTATION_without_the_deny_list_a_declared_cost_tier_lifts_to_PASS(tree, monkeypatch):
    sql, cols, decl = "SELECT id, cost_tier FROM t_dens", ["id", "cost_tier"], {"t_dens": ["cost_tier"]}
    assert _v(_scan(tree, sql, cols, decl))["v"] == PARTIAL
    monkeypatch.setattr(ac, "DENS_TIER_DENY_WORDS", frozenset())
    assert _v(_scan(tree, sql, cols, decl))["v"] == PASS
    assert ac.density_tier_problem({"density_tier_columns": [dict(ENT, column="cost_tier")]}) is None       # and the validator would accept the declaration


def test_MUTATION_without_the_declaration_a_confidence_tier_never_counts(tree):
    sql, cols = "SELECT id, confidence_tier FROM t_dens", ["id", "confidence_tier"]
    assert _v(_scan(tree, sql, cols, {"t_dens": ["confidence_tier"]}))["v"] == PASS
    assert _v(_scan(tree, sql, cols, None))["v"] == PARTIAL                                                 # the declaration is what lifts it


def test_MUTATION_the_exact_names_are_the_only_undeclared_vocabulary(monkeypatch):
    assert not ac.dens_tier_counts("confidence_tier")
    monkeypatch.setattr(ac, "DENS_TIER_EXACT", frozenset({"tier", "verification_pass_status", "confidence_tier"}))
    assert ac.dens_tier_counts("confidence_tier")                                                           # widening the closed list is a registry change, caught here and by the pin


# ═════════════════════════ the declaration validator ═════════════════════════

def test_a_valid_declaration_is_accepted_alone_and_in_a_list():
    ac.validate_declarations(_doc(dict(density_tier_columns=[dict(ENT)])))
    ac.validate_declarations(_doc(dict(density_tier_columns=[dict(ENT), dict(ENT, column="evidence_grade_tier", why="verification grade of the row's evidence chain, a tier")])))
    assert ac.density_tier_problem({}) is None and ac.density_tier_problem({"density_tier_columns": None}) is None       # absent / null = declares none
    assert ac.density_tier_problem(None) is None


@pytest.mark.parametrize("dt, match", [
    ({}, "non-empty list"), ("confidence_tier", "non-empty list"), ([], "non-empty list"), (7, "non-empty list"),
    (["confidence_tier"], r"density_tier_columns\[0\] must be an object"), ([7], r"must be an object"),
    ([dict(ENT, extra=1)], "unknown field"),
    ([dict(column="confidence_tier", why=WHY)], "missing field"), ([dict(column="confidence_tier", evidence=EVID)], "missing field"), ([dict(why=WHY, evidence=EVID)], "missing field"),
    ([dict(ENT, column="a b")], r"\.column must be a column name"), ([dict(ENT, column='c"')], r"\.column must be a column name"), ([dict(ENT, column="")], r"\.column must be a column name"),
    ([dict(ENT, column=3)], r"\.column must be a column name"), ([dict(ENT, column=None)], r"\.column must be a column name"),
    ([dict(ENT), dict(ENT)], "declared twice"), ([dict(ENT), dict(ENT, column="CONFIDENCE_TIER")], "declared twice"),
    ([dict(ENT, column=f"c{i}") for i in range(17)], "not a tier vocabulary"),
])
def test_validator_refuses_a_malformed_list(dt, match):
    _bad(dt, match)


@pytest.mark.parametrize("name", DENIED_NAMES)
def test_validator_refuses_a_deny_listed_declared_column(name):
    _bad([dict(ENT, column=name)], "deny-listed word")


def test_the_deny_list_message_names_the_word():
    _bad([dict(ENT, column="cost_tier")], "'cost'")
    _bad([dict(ENT, column="access_tier")], "'access'")


@pytest.mark.parametrize("why, match", [
    ("", r"\.why"), ("  ", r"\.why"), ("N/A", r"\.why"), ("two words", r"\.why"), ("TBD confidence tier of the row", r"\.why"), ("a\nconfidence tier line break", r"\.why"),
    (" confidence tier of the served row ", r"\.why"), (7, r"\.why"), (None, r"\.why"), ("x" * 1201, r"\.why"),
    ("a bucket of the served row for the viewer", "verification or confidence"),                           # a real sentence that says nothing about verification / confidence
    ("cost bucket the buyer pays for the row", "verification or confidence"),
    # F3 (review of PR 3037): the keyword is present but the reason is about price / cost: refused on the deny word
    ("price bucket the buyer pays, nothing to do with verification", "deny-listed word 'price'"),
    ("cost band for the viewer, not a confidence tier of anything", "deny-listed word 'cost'"),
    ("a verification tier, shown to the Plan viewers", "deny-listed word 'plan'"), ("confidence tier, Prices of the remedy", "deny-listed word 'price'"),
    ("verification tier: which Subscription may read the row", "deny-listed word 'subscription'"), ("a confidence tier, not the access level", "deny-listed word 'access'"),
])
def test_validator_refuses_a_weak_why(why, match):
    _bad([dict(ENT, why=why)], match)


@pytest.mark.parametrize("why", ["verification tier of the served row", "Confidence grade of the row, the tier of its reading", "the row's CONFIDENCE tier, graded by the writer"])
def test_validator_accepts_a_why_that_says_verification_or_confidence(why):
    ac.validate_declarations(_doc(dict(density_tier_columns=[dict(ENT, why=why)])))


@pytest.mark.parametrize("ev, match", [
    ("unverified:somewhere I read it last week", "unverified"), ("unverified:", "unverified"),
    ("platform/scripts/governance/nonexistent_file_xyz.py:3", "not an existing repo-relative file"),
    ("platform/scripts/governance/__tests__/test_e6_dens_tier_guard.py", "must name a line"),                                   # a real file, no line
    ("platform/scripts/governance/ci_shard.py:1", "does not mention 'confidence_tier'"),                   # F3: a real file:line that is about something else
    ("platform/scripts/governance/asset_census.py:0", "names line 0"), ("platform/scripts/governance/asset_census.py:99999999", "names line"),
    ("/etc/hosts:1", "not an existing repo-relative file"), ("../outside.py:1", "not an existing repo-relative file"),
    ("platform/scripts/governance/../governance/asset_census.py:1", "not an existing repo-relative file"),
    ("", "not a non-blank string"), ("  ", "not a non-blank string"), (7, "not a non-blank string"), (None, "not a non-blank string"),
    ("platform/scripts/governance/asset_census.py:1\u200b", "control or invisible"),
])
def test_validator_refuses_an_unverifiable_evidence(ev, match):
    _bad([dict(ENT, evidence=ev)], match)


def test_the_evidence_standard_is_the_shared_helper_not_a_copy(monkeypatch):
    """ONE definition: a stub of the S3 helper changes this declaration's verdict, so the check is that helper's, not a private copy."""
    seen = []
    monkeypatch.setattr(ac, "_s3_evidence_problem", lambda ev, *, allow_unverified, needle=None: seen.append((ev, allow_unverified, needle)) or "is rejected by the shared helper")
    _bad([dict(ENT)], "rejected by the shared helper")
    assert seen == [(EVID, False, "confidence_tier")]
    src = inspect.getsource(ac.density_tier_problem)
    assert "_s3_evidence_problem" in src and "_s3_text_problem" in src and "_evidence_pointer_ok(" not in src


def test_MUTATION_the_validator_guards_each_bite(monkeypatch):
    """Switch a guard off and the declaration it exists to refuse is accepted."""
    bad_ev = dict(ENT, evidence="platform/scripts/governance/nonexistent_file_xyz.py:3")
    assert ac.density_tier_problem({"density_tier_columns": [bad_ev]})
    monkeypatch.setattr(ac, "_s3_evidence_problem", lambda ev, *, allow_unverified, needle=None: None)
    assert ac.density_tier_problem({"density_tier_columns": [bad_ev]}) is None                              # evidence guard off: accepted
    weak = dict(ENT, why="N/A")
    monkeypatch.setattr(ac, "_s3_text_problem", lambda *a, **k: None)
    assert ac.density_tier_problem({"density_tier_columns": [dict(weak, why="a bucket of the row for the viewer")]})         # the 'says verification' guard is separate and still bites
    assert ac.density_tier_problem({"density_tier_columns": [weak]})                                       # ... and so does the missing word (N/A has neither)
    monkeypatch.setattr(ac, "DENSITY_TIER_WHY_WORDS", ("",))
    assert ac.density_tier_problem({"density_tier_columns": [dict(weak, why="a bucket of the row for the viewer")]}) is None    # words guard off: accepted


def test_the_validator_is_reached_from_validate_declarations_and_the_load_path(tmp_path):
    p = tmp_path / "d.json"
    doc = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    doc["assets"]["bg_remedies"]["density_tier_columns"] = [dict(ENT, column="cost_tier")]
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ac.DeclarationsError, match="cost_tier.*deny-listed"):
        ac.load_asset_declarations(p)
    doc["assets"]["bg_remedies"]["density_tier_columns"] = [dict(ENT)]
    p.write_text(json.dumps(doc), encoding="utf-8")
    assert ac.load_asset_declarations(p)["bg_remedies"]["density_tier_columns"][0]["column"] == "confidence_tier"
    doc["density_tier_declaration_fields"] = ["column", "why"]
    p.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(ac.DeclarationsError, match="density_tier_declaration_fields"):
        ac.load_asset_declarations(p)


def test_the_column_must_be_in_the_table_the_check_the_measure_glue_runs():
    e = {"density_tier_columns": [dict(ENT)]}
    assert ac.density_tier_problem(e, ["id", "confidence_tier"]) is None
    assert ac.density_tier_problem(e, ["id", "CONFIDENCE_TIER"]) is None                                     # catalog names are case-insensitive here, as the scan is
    assert "not columns of the asset's table" in ac.density_tier_problem(e, ["id", "tier"])
    assert "not columns of the asset's table" in ac.density_tier_problem(e, [])
    assert ac.density_tier_problem(e, None) is None                                                         # no catalog: the validator's shape check only


# ═════════════════════════ measure(): the glue (offline) ═════════════════════════

def _measure_with(monkeypatch, tree, sql, table_cols, entry):
    tree.write(tree.layers / "L0_x", "q.ts", dr._cap(sql))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: ({"bg_x": entry} if entry is not None else {}))
    return dr._dens(dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (list(table_cols), [])}), "bg_x")


def test_measure_an_undeclared_confidence_tier_is_PARTIAL(monkeypatch, tree):
    d = _measure_with(monkeypatch, tree, "SELECT fact_id, confidence_tier FROM t_x", ["fact_id", "confidence_tier"], None)
    assert d["v"] == PARTIAL and "no tier column" in d["measured"], d


def test_measure_a_declared_confidence_tier_is_PASS_and_named(monkeypatch, tree):
    d = _measure_with(monkeypatch, tree, "SELECT fact_id, confidence_tier FROM t_x", ["fact_id", "confidence_tier"], dict(kind="data", density_tier_columns=[dict(ENT)]))
    assert d["v"] == PASS and "confidence_tier" in d["measured"], d


def test_measure_a_declared_cost_tier_never_reaches_PASS(monkeypatch, tree):
    """The validator refuses it; were a refused declaration to reach measure() (a bypass), the glue refuses it too: NO_DETECTOR, never PASS."""
    d = _measure_with(monkeypatch, tree, "SELECT fact_id, cost_tier FROM t_x", ["fact_id", "cost_tier"], dict(kind="data", density_tier_columns=[dict(ENT, column="cost_tier")]))
    assert d["v"] == NO_DET and "deny-listed" in d["measured"] and "never PASS" in d["measured"], d


def test_measure_a_declared_column_the_table_lacks_reads_NO_DETECTOR_with_the_disagreement(monkeypatch, tree):
    d = _measure_with(monkeypatch, tree, "SELECT fact_id, confidence_tier FROM t_x", ["fact_id"], dict(kind="data", density_tier_columns=[dict(ENT)]))
    assert d["v"] == NO_DET and "not columns of the asset's table" in d["measured"] and "confidence_tier" in d["measured"], d


def test_MUTATION_without_the_measure_time_refusal_a_refused_declaration_reads_PARTIAL_not_NO_DETECTOR(monkeypatch, tree):
    """The measure-time check is what reports a refused declaration instead of grading silently on the closed default."""
    entry = dict(kind="data", density_tier_columns=[dict(ENT)])
    assert _measure_with(monkeypatch, tree, "SELECT fact_id, confidence_tier FROM t_x", ["fact_id"], entry)["v"] == NO_DET
    monkeypatch.setattr(ac, "density_tier_problem", lambda *a, **k: None)
    d = _measure_with(monkeypatch, tree, "SELECT fact_id, confidence_tier FROM t_x", ["fact_id"], entry)
    assert d["v"] == PARTIAL and "refused" not in d["measured"], d


def test_F1_a_declared_column_on_a_table_with_no_catalog_columns_is_unverifiable_NO_DETECTOR(monkeypatch, tree):
    """Review F1: a view / materialized view lists no columns in information_schema, so the existence check used to be skipped and a declared `no_such_col` read PASS."""
    entry = dict(kind="data", density_tier_columns=[dict(ENT, column="no_such_col")])
    tree.write(tree.layers / "L0_x", "q.ts", dr._cap("SELECT fact_id, no_such_col FROM t_x"))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"bg_x": entry})
    d = dr._dens(dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": ([], [])}), "bg_x")
    assert d["v"] == NO_DET and "table columns unknown" in d["measured"] and "declaration unverifiable" in d["measured"] and "never PASS" in d["measured"], d


def test_F1_a_declaration_on_an_asset_with_no_target_table_says_so_never_silently_PARTIAL(monkeypatch, tree):
    entry = dict(kind="service", density_tier_columns=[dict(ENT)])
    tree.write(tree.layers / "L0_x", "q.ts", dr._cap("SELECT fact_id, confidence_tier FROM bg_x"))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"bg_x": entry})
    d = dr._dens(dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", None, asset_kind="service")}, {}), "bg_x")
    assert d["v"] == NO_DET and "no target table" in d["measured"] and "declaration unverifiable" in d["measured"], d


def test_F1_the_measure_problem_is_the_validators_check_plus_what_only_a_measurement_can_say():
    e = {"density_tier_columns": [dict(ENT)]}
    assert ac.density_tier_measure_problem({}, "t", ["id"]) is None and ac.density_tier_measure_problem(None, None, None) is None
    assert "no target table" in ac.density_tier_measure_problem(e, None, ["confidence_tier"]) and "no target table" in ac.density_tier_measure_problem(e, "", None)
    assert "table columns unknown" in ac.density_tier_measure_problem(e, "t", None)
    assert "not columns of the asset's table" in ac.density_tier_measure_problem(e, "t", ["id"])
    assert ac.density_tier_measure_problem(e, "t", ["confidence_tier"]) is None
    assert "deny-listed" in ac.density_tier_measure_problem({"density_tier_columns": [dict(ENT, column="cost_tier")]}, "t", ["cost_tier"])


def test_MUTATION_without_the_unknown_columns_refusal_the_declared_ghost_column_would_not_be_refused(monkeypatch):
    e = {"density_tier_columns": [dict(ENT, column="no_such_col")]}
    assert ac.density_tier_measure_problem(e, "t_x", None)                                               # the guard (F1)
    monkeypatch.setattr(ac, "density_tier_measure_problem", lambda entry, table, cols: ac.density_tier_problem(entry, cols))
    assert ac.density_tier_measure_problem(e, "t_x", None) is None                                       # the old glue: columns None skipped the check


def test_F4_the_refusal_text_names_what_the_scan_graded_on_the_closed_default(monkeypatch, tree):
    """M28: the NO_DETECTOR record says what the cell WOULD have read on the closed default, so a reviewer sees the refusal did not hide a verdict."""
    entry = dict(kind="data", density_tier_columns=[dict(ENT)])
    d = _measure_with(monkeypatch, tree, "SELECT fact_id, confidence_tier FROM t_x", ["fact_id"], entry)
    assert d["v"] == NO_DET and "(graded on that default: PARTIAL)" in d["measured"], d
    d = _measure_with(monkeypatch, tree, "SELECT fact_id, tier FROM t_x", ["fact_id", "tier"], dict(kind="data", density_tier_columns=[dict(ENT, column="no_such_col")]))
    assert d["v"] == NO_DET and "(graded on that default: PASS)" in d["measured"], d


def test_F4_the_deny_check_runs_on_every_entry_not_only_the_first():
    """M31: a clean first entry must not let a deny-listed later entry through."""
    ok = dict(ENT, column="evidence_grade_tier", why="verification grade of the row's evidence chain, a tier")
    _bad([ok, dict(ENT, column="cost_tier")], r"density_tier_columns\[1\]\.column 'cost_tier' carries the deny-listed word 'cost'")
    _bad([ok, dict(ENT), dict(ENT, column="priceTier")], r"density_tier_columns\[2\]\.column 'priceTier'")
    _bad([ok, dict(ENT, why="cost band for the viewer, not a confidence tier of anything")], r"density_tier_columns\[1\]\.why contains the deny-listed word 'cost'")
    _bad([ok, dict(ENT, evidence="platform/scripts/governance/ci_shard.py:1")], r"density_tier_columns\[1\]\.evidence")


def test_F3_the_s3_helper_needle_is_optional_and_s3_behaviour_is_unchanged():
    f = "platform/scripts/governance/ci_shard.py:1"
    assert ac._s3_evidence_problem(f, allow_unverified=False) is None                                    # no needle: exactly S3's behaviour
    assert ac._s3_evidence_problem(f, allow_unverified=False, needle="ci_shard") is None
    assert "does not mention" in ac._s3_evidence_problem(f, allow_unverified=False, needle="confidence_tier")
    assert ac._s3_evidence_problem(f, allow_unverified=False, needle="CI_SHARD") is None                 # case-insensitive
    assert "not an existing" in ac._s3_evidence_problem("platform/scripts/governance/nope.py:1", allow_unverified=False, needle="x")   # S3's own checks first


def test_MUTATION_without_the_needle_and_the_why_deny_a_price_declaration_is_accepted(monkeypatch):
    e = {"density_tier_columns": [dict(ENT, column="bucket_tier", why="price bucket the buyer pays, nothing to do with verification")]}
    assert "deny-listed word 'price'" in ac.density_tier_problem(e)
    monkeypatch.setattr(ac, "DENS_TIER_DENY_WORDS", frozenset())
    assert ac.density_tier_problem(e) is None                                                            # why guard off: accepted
    other = {"density_tier_columns": [dict(ENT, evidence="platform/scripts/governance/ci_shard.py:1")]}
    monkeypatch.undo()
    assert "does not mention" in ac.density_tier_problem(other)
    monkeypatch.setattr(ac, "_s3_evidence_problem", lambda ev, *, allow_unverified, needle=None: None)
    assert ac.density_tier_problem(other) is None                                                        # needle guard off: accepted


def test_measure_a_declaration_does_not_leak_to_another_asset(monkeypatch, tree):
    tree.write(tree.layers / "L0_x", "q.ts", dr._cap("SELECT fact_id, confidence_tier FROM t_x"))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"bg_y": dict(kind="data", density_tier_columns=[dict(ENT)])})
    d = dr._dens(dr._measure(monkeypatch, tree, {"bg_x": w1._reg_row("bg_x", "t_x")}, {"t_x": (["fact_id", "confidence_tier"], [])}), "bg_x")
    assert d["v"] == PARTIAL, d


# ═════════════════════════ REAL_SQL: the column list comes from the census's own catalog() on a real Postgres ═════════════════════════

TABLE = "dens_guard_t"
ALL_TIERS = ["tier", "verification_pass_status", "cost_tier", "access_tier", "price_tier", "severity_tier", "confidence_tier", "plan_tier", "signature_tier"]


@pytest.fixture
def real_cols(monkeypatch, disposable_pg):
    """The table's columns exactly as the census reads them (`catalog()` over information_schema), from a throw-away cluster."""
    point_psql_at(disposable_pg, monkeypatch)
    disposable_pg.psql(f"DROP TABLE IF EXISTS {TABLE}")
    disposable_pg.psql(f"CREATE TABLE {TABLE} (id int, {', '.join(c + ' text' for c in ALL_TIERS)}, note text)")
    try:
        cat = _REAL_CATALOG([TABLE])
        assert cat["exists"] == {TABLE}, cat
        yield cat["cols"][TABLE]
    finally:
        disposable_pg.psql(f"DROP TABLE IF EXISTS {TABLE}")


def test_REAL_SQL_the_catalog_columns_are_the_real_ones(real_cols):
    assert real_cols == ["id"] + ALL_TIERS + ["note"]


@pytest.mark.parametrize("col, counts", [("tier", True), ("verification_pass_status", True), ("cost_tier", False), ("access_tier", False), ("price_tier", False),
                                         ("severity_tier", False), ("confidence_tier", False), ("plan_tier", False), ("signature_tier", False), ("note", False)])
def test_REAL_SQL_which_real_columns_count(tree, real_cols, col, counts):
    d = _v(_scan(tree, f"SELECT id, {col} FROM {TABLE}", real_cols, table=TABLE))
    assert (d["v"] == PASS) is counts, (col, d)


def test_REAL_SQL_select_star_over_the_real_columns_credits_only_tier_and_verification_pass_status(tree, real_cols):
    cap = _scan(tree, f"SELECT * FROM {TABLE}", real_cols, table=TABLE)
    assert cap["dense"] == [("L0_x/q.ts", ["tier", "verification_pass_status"])], cap["dense"]


def test_REAL_SQL_a_declared_confidence_tier_counts_only_with_a_valid_declaration_and_never_a_denied_one(tree, real_cols):
    sql = f"SELECT id, confidence_tier FROM {TABLE}"
    assert _v(_scan(tree, sql, real_cols, table=TABLE))["v"] == PARTIAL
    assert _v(_scan(tree, sql, real_cols, declared={TABLE: ["confidence_tier"]}, table=TABLE))["v"] == PASS
    for col in ("cost_tier", "access_tier", "price_tier", "plan_tier"):
        d = _v(_scan(tree, f"SELECT id, {col} FROM {TABLE}", real_cols, declared={TABLE: [col]}, table=TABLE))
        assert d["v"] == PARTIAL, (col, d)
    e = {"density_tier_columns": [dict(ENT)]}
    assert ac.density_tier_problem(e, real_cols) is None
    assert ac.density_tier_problem({"density_tier_columns": [dict(ENT, column="no_such_tier")]}, real_cols)


def test_REAL_SQL_measure_end_to_end_on_the_real_catalog(monkeypatch, tree, real_cols):
    """measure() with the REAL catalog() (the stub only fixes the registry and the unrelated reads): cost_tier PARTIAL, declared confidence_tier PASS, a declared
    column the real table lacks NO_DETECTOR."""
    def run(sql, entry):
        tree.write(tree.layers / "L0_x", "q.ts", dr._cap(sql))
        monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: ({"bg_x": entry} if entry is not None else {}))
        w1._stub_layer(monkeypatch, tree.tmp, {"bg_x": w1._reg_row("bg_x", TABLE)}, {TABLE: (real_cols, [])})
        monkeypatch.setattr(ac, "catalog", _REAL_CATALOG)                                                    # the real read, over the disposable cluster
        monkeypatch.setattr(ac, "live_counts", lambda *a, **k: ({}, {}))
        monkeypatch.setattr(ac, "capability_scan", dr._REAL_SCAN)
        monkeypatch.setattr(ac, "CAPS_ROOTS", tree.roots)
        monkeypatch.setattr(ac, "DENS_OUTSIDE_ROOTS", ())
        monkeypatch.setattr(ac, "depth_census", lambda t, c: dict(columns=len(c), rows=3, full=list(c), never=[], note=""))
        return dr._dens(ac.measure("L0"), "bg_x")
    assert run(f"SELECT id, cost_tier FROM {TABLE}", None)["v"] == PARTIAL
    assert run(f"SELECT id, cost_tier FROM {TABLE}", dict(kind="data", density_tier_columns=[dict(ENT, column="cost_tier")]))["v"] == NO_DET
    assert run(f"SELECT id, confidence_tier FROM {TABLE}", None)["v"] == PARTIAL
    assert run(f"SELECT id, confidence_tier FROM {TABLE}", dict(kind="data", density_tier_columns=[dict(ENT)]))["v"] == PASS
    assert run(f"SELECT id, confidence_tier FROM {TABLE}", dict(kind="data", density_tier_columns=[dict(ENT, column="no_such_tier")]))["v"] == NO_DET
    assert run(f"SELECT id, tier FROM {TABLE}", None)["v"] == PASS


# ═════════════════════════ one definition across consumers, the pins, the real tree ═════════════════════════

def test_one_definition_the_census_is_the_only_place_a_tier_name_is_classified():
    gov = HERE.parent
    ctrl = gov.parents[2] / "00_ARCHITECTURE" / "control"
    for f in list(gov.glob("*.py")) + list(ctrl.glob("*.py")):
        src = f.read_text(encoding="utf-8")
        assert "DENS_TIER_COLUMN" not in src, f"{f.name}: the old open regex name must be gone everywhere"
        if f.name != "asset_census.py":
            assert not re.search(r"\\w\+_tier", src), f"{f.name} must not carry its own tier-name pattern"
            assert "dens_tier_counts" not in src, f"{f.name}: consumers read the census's verdicts; they never re-classify a name"
    body = inspect.getsource(ac._select_tier)
    assert body.count("dens_tier_counts(") == 2 and "re.compile" not in body and ".match(" not in body.split('"""', 2)[2]      # the two item checks, no pattern of its own


def test_the_pin_the_revision_the_criterion_and_the_declarations_file():
    assert ac.REGISTRY_REVISION >= 23 and 23 in p1.PINNED_FINGERPRINTS
    assert p1.PINNED_FINGERPRINTS[23] and len(p1.PINNED_FINGERPRINTS[23]) == 64
    e = ac.CRITERION_REGISTRY["Dens.served"]
    assert e["revision"] == 6
    for phrase in ("CLOSED list", "exactly `tier` or `verification_pass_status`", "density_tier_columns", "deny-listed", "cost, price, pricing, plan, access, subscription, billing, fee, tariff",
                   "severity_tier, cost_tier, access_tier"):
        assert phrase.replace("CLOSED list", "closed list") in e["applicability"] or phrase in e["applicability"], phrase
    src = pathlib.Path(ac.__file__).read_text(encoding="utf-8")
    assert "23 (provisional): DENS-TIER-GUARD" in src.split("REGISTRY_REVISION = ", 1)[1].split("\n", 1)[0]
    raw = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    assert raw["version"] == "1.13.0" and raw["density_tier_declaration_fields"] == ["column", "why", "evidence"] == list(ac.DENS_TIER_DECL_FIELDS)
    assert "density_tier_columns" in raw["description"] and "N-98" in raw["description"]
    assert [a for a, d in raw["assets"].items() if "density_tier_columns" in d] == [], "inert: no asset declares one yet"


def test_only_dens_served_changed_in_the_criterion_registry_at_23():
    assert {k for k, v in ac.CRITERION_REGISTRY.items() if v["revision"] == 6} == {"Dens.served"}
    assert set(ac.NA_CAUSES["Dens.served"]) == {"no-served-surface"} and list(r for r in ac.NA_RULE_DECISIONS if r.startswith("Dens.served")) == ["Dens.served#measured:no-served-surface"]


def test_the_real_tree_moves_exactly_three_pass_cells_to_partial_and_nothing_else(monkeypatch):
    """The measured effect of the closed list on the committed 127-asset inputs (they re-measure to the saved censuses of adb0db2 on 126 of 127 assets). The three are
    the assets whose PASS rested on a `*_tier` column outside the vocabulary and with no declaration; each is an SS decision (declare it, or accept PARTIAL)."""
    import test_e6_dens_label_select as ls
    new_fn = ac.dens_tier_counts
    real_read, cache = pathlib.Path.read_text, {}

    def cached(self, *a, **k):                                          # the two scans read the same ~1.5k files: read each once
        key = (str(self), a, tuple(sorted(k.items())))
        if key not in cache:
            cache[key] = real_read(self, *a, **k)
        return cache[key]
    monkeypatch.setattr(pathlib.Path, "read_text", cached)

    def scan():
        out = {}
        for d in ls.FX["layers"].values():
            for r in d["assets"]:
                # only an asset whose scanned tables hold a `*_tier` column outside the closed list CAN differ (the two vocabularies agree on every other name): scan those
                if not any(OLD_OPEN.match(c) and c.lower() not in ac.DENS_TIER_EXACT for tk in r["tokens"] for c in (d["columns"].get(tk.lower()) or d["columns"].get(tk) or [])):
                    continue
                cap = ac.capability_scan(ac.CAPS_ROOTS, r["tokens"], shared=frozenset(d["shared"]), columns=d["columns"], outside_roots=ac.DENS_OUTSIDE_ROOTS,
                                         service=(r.get("asset_kind") == "service"))
                out[r["asset_id"]] = ac._grade_dens(cap, r["target_table"] or r["asset_id"])["v"]
        return out
    new = scan()
    monkeypatch.setattr(ac, "dens_tier_counts", lambda n, d=(): bool(OLD_OPEN.match(n)))
    old = scan()
    monkeypatch.setattr(ac, "dens_tier_counts", new_fn)
    assert set(old) == set(new) and len(old) >= 9                                              # the candidate assets (a `*_tier` column outside the closed list), both ways
    moved = {a: (old[a], new[a]) for a in old if old[a] != new[a]}
    assert moved == {"ga_medical": (PASS, PARTIAL), "ga_vastu": (PASS, PARTIAL), "mi_kula": (PASS, PARTIAL)}, moved


def test_bg_remedies_cost_tier_is_not_a_tier_column_on_the_real_inputs():
    """The ruling's own example: bg_remedies reads brahma_remedy_corpus, which has a `cost_tier` price bucket. Under the closed list it never counts."""
    import test_e6_dens_label_select as ls
    cols = ls.FX["layers"]["L0"]["columns"]["brahma_remedy_corpus"]
    assert "cost_tier" in cols
    state, got = ac._select_tier("*", None, "brahma_remedy_corpus", cols)
    assert "cost_tier" not in got and set(got) <= {"tier", "verification_pass_status"}, (state, got)
    assert ac._select_tier("cost_tier", None, "brahma_remedy_corpus", cols) == (ac.TIER_NO, [])
