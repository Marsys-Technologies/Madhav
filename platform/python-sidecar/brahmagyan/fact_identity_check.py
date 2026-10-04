"""
fact_identity_check.py — the corrected G-IDX check and the pure per-fact
3-way classifier used by `scripts/build_fact_identity_index.py`.

Why this exists (S-L1 rehearsal P3, 2026-10-03): the standalone G-IDX script
used to *print* parsed / identity_free / gap and leave "is that good enough?"
to a human reading the output against a number in a runbook. The rehearsal
showed the number drifting ("gap <= 15 known", then 3,411 after the S-L1
rebuilds added categories with no rule) with nothing in code to say so. This
module makes the verdict a function, with a detector behind every clause
(CLAUDE.md N.8 — a status is computed by a detector that measures the claim,
or it is null).

The corrected check (W7 abort rule, as AMENDED by SS, 2026-10-03):

  rows_equal_parsed                 rows in chart_fact_identity == parsed
  partition_sums_to_total           parsed + identity_free + gap == total chart_facts rows
  reason_counts_sum_to_identity_free  sum(per-reason counts) == identity_free
  gap_within_limit                  gap <= 0   (target is ZERO; the old "15 known" is retired)
  coverage_of_identity_bearing      parsed / (parsed + gap) >= 99.98 %
  identity_free_reason_set          observed identity_free reasons == the allowed set
                                    (the 14 pre-S-L1 reasons + 'scope_cap_sentinel');
                                    ANY other reason aborts
  facts_present                     the chart has at least one chart_facts row

A clause that could not be measured (rows_equal_parsed in a dry-run, where
nothing is written) is `None` = NOT EVALUATED, never green.

This module is imported ONLY by the standalone script and its tests; it is not
on any registered writer's import closure (it must stay that way: a writer
importing it would move that writer's provenance digest).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from brahmagyan.fact_identity_parser import (
    SCOPE_CAP_SENTINEL_REASON,
    classify_unparsed_subject,
    parse_fact_identity,
)

# ── the identity_free reason set: explicit and versioned ──────────────────
REASON_SET_VERSION = "v2 (2026-10-03): the 14 reasons measured on the S-L1 rehearsal + 'scope_cap_sentinel' (SS ruling)"

# The 14 reasons observed on the rehearsal end state (rehearsal_final/out/
# gidx_final_reasons.txt). 'yoga_or_dosha_catalog_label' is deliberately NOT
# in this set: it is reachable in code but was never observed, and the SS rule
# is equality with what was MEASURED, not with what the classifier could say.
IDENTITY_FREE_REASONS_V1 = frozenset({
    "ashtakavarga_kakshya_index_not_house",
    "ayurdaya_method_label",
    "bhrigu_nadi_chakra_index_not_house",
    "dhaiya_subperiod_label_moon_relative_not_lagna_house",
    "dosha_label_catalog_label",
    "fixed_reference_lookup_table_row_not_natal_placement",
    "jaimini_karaka_role_label",
    "nakshatra_name_fifth_dimension_out_of_scope",
    "panchanga_constant_label",
    "sade_sati_cycle_phase_label_moon_relative_not_lagna_house",
    "saham_arabic_part_label",
    "special_point_or_aggregate_marker",
    "tajik_hadda_degree_term_index_not_house",
    "yoga_label_catalog_label",
})

# The ONE amendment. Any further reason needs a new, explicit, versioned edit here.
IDENTITY_FREE_REASONS_ALLOWED = IDENTITY_FREE_REASONS_V1 | frozenset({SCOPE_CAP_SENTINEL_REASON})

MAX_GAP = 0
MIN_COVERAGE_PCT = 99.98


# ── per-fact 3-way partition ──────────────────────────────────────────────
def classify_fact(fact_category: str | None, fact_subject: str | None, fact_key: str | None):
    """Partition one chart_facts row into exactly one of:

      ("parsed", IdentityMatch)     identity extracted
      ("identity_free", reason)     a RECOGNISED token that carries no identity
      ("gap", None)                 neither -> surfaces in the gap count + examples

    There is no fourth bucket and no default-to-identity_free: an unknown
    category/subject is a gap by construction.
    """
    match = parse_fact_identity(fact_subject, fact_key, fact_category)
    if match is not None:
        return "parsed", match
    reason = classify_unparsed_subject(fact_subject or "", fact_category)
    if reason is not None:
        return "identity_free", reason
    return "gap", None


# ── the check ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class CheckItem:
    name: str
    passed: bool | None  # None = not evaluated (no detector ran)
    detail: str


@dataclass(frozen=True)
class CheckResult:
    items: tuple[CheckItem, ...]

    @property
    def failed(self) -> list[CheckItem]:
        return [i for i in self.items if i.passed is False]

    @property
    def not_evaluated(self) -> list[CheckItem]:
        return [i for i in self.items if i.passed is None]

    @property
    def ok(self) -> bool:
        return not self.failed and not self.not_evaluated

    def render(self) -> str:
        def tag(i: CheckItem) -> str:
            return {True: "PASS", False: "FAIL", None: "NOT_EVALUATED"}[i.passed]
        return "\n".join(f"  [{tag(i)}] {i.name}: {i.detail}" for i in self.items)


def check_identity_index(
    summary: Mapping[str, Any],
    *,
    expected_reasons: frozenset[str] = IDENTITY_FREE_REASONS_ALLOWED,
    exact_reasons: bool = True,
    max_gap: int = MAX_GAP,
    min_coverage_pct: float = MIN_COVERAGE_PCT,
) -> CheckResult:
    """Evaluate the corrected G-IDX check on a `build_index_for_chart` summary.

    `summary` needs: total_facts, parsed, identity_free, gap,
    identity_free_reasons (dict reason -> count) and rows_in_table (count of
    chart_fact_identity rows for the chart AFTER the insert, or None when
    nothing was written).

    exact_reasons=True  (default, the SS rule): observed reasons == expected.
    exact_reasons=False: observed reasons <= expected (a reason that simply did
        not occur on this chart is tolerated; a NEW reason still fails). For
        charts that were not rebuilt with every S-L1 writer.
    """
    total = int(summary["total_facts"])
    parsed = int(summary["parsed"])
    identity_free = int(summary["identity_free"])
    gap = int(summary["gap"])
    counts = dict(summary.get("identity_free_reasons") or {})
    rows = summary.get("rows_in_table")

    items: list[CheckItem] = []

    present_ok = total > 0
    items.append(CheckItem("facts_present", present_ok, f"total_facts={total}"))

    if rows is None:
        items.append(CheckItem("rows_equal_parsed", None, f"rows_in_table not measured (dry-run); parsed={parsed}"))
    else:
        rows_ok = rows == parsed
        items.append(CheckItem("rows_equal_parsed", rows_ok, f"rows={rows} parsed={parsed}"))

    sum_ok = parsed + identity_free + gap == total
    items.append(CheckItem(
        "partition_sums_to_total", sum_ok,
        f"parsed({parsed}) + identity_free({identity_free}) + gap({gap}) = {parsed + identity_free + gap} vs total {total}",
    ))

    reason_sum_ok = sum(counts.values()) == identity_free
    items.append(CheckItem(
        "reason_counts_sum_to_identity_free", reason_sum_ok,
        f"sum(reason counts)={sum(counts.values())} identity_free={identity_free}",
    ))

    gap_ok = gap <= max_gap
    items.append(CheckItem("gap_within_limit", gap_ok, f"gap={gap} limit={max_gap}"))

    denom = parsed + gap
    coverage_pct = (100.0 * parsed / denom) if denom else 100.0
    coverage_ok = coverage_pct >= min_coverage_pct
    items.append(CheckItem(
        "coverage_of_identity_bearing", coverage_ok,
        f"coverage={coverage_pct:.4f}% threshold={min_coverage_pct}%",
    ))

    observed = {r for r, n in counts.items() if n}
    expected = set(expected_reasons)
    if exact_reasons:
        reasons_ok = observed == expected
    else:
        reasons_ok = observed <= expected
    items.append(CheckItem(
        "identity_free_reason_set", reasons_ok,
        f"mode={'exact' if exact_reasons else 'subset'} observed={len(observed)} expected={len(expected)} "
        f"unexpected={sorted(observed - expected)} missing={sorted(expected - observed)} "
        f"set_version={REASON_SET_VERSION!r}",
    ))

    return CheckResult(tuple(items))
