#!/usr/bin/env python3
"""
apply_tci_fixups_omega8.py — Elevation Campaign v2.1, Stream γ (PŪRṆA), Lane Ω8.

Three small, well-scoped, TAGGED metadata corrections to the already-merged Ω1 TCI
(TOTAL_CONCEPT_INVENTORY_v1_0.json), bundled into ONE follow-up patch per the γ proxy
ruling (CMN-1 / CMN-2 / Ω5's serving_args mismatch → all tagged Ω8-fixup):

  Ω8-fixup : ganita_chart_facts_get's serving_args records `fact_category`, but the live
             tool's actual parameter name is `category`. Rename the KEY (value/position
             preserved) for every affected entry. ~12,200+ entries — the dominant wealth-
             serving tool — so before/after counts are asserted.

  CMN-1    : mechanism-class TCI entries (serving_tool bodha_mechanisms_get) have
             row_count_per_canonical_chart SUMMED across all 5 ayanamshas, while the live
             tool defaults to one (lahiri). Add `is_ayanamsha_summed: true` + a concise
             note so a downstream consumer never misreads the number as per-ayanamsha.

  CMN-2    : the contradiction-pole concept (l2.contradiction_pole.domain_promise_vs_denial)
             points serving_tool at bodha_quality_get (a scorecard summary). Repoint to
             bodha_graph_subgraph_get with serving_args reflecting mode=contradictions
             (the tool that actually serves the pole rows) — Ω6 charter-item evidence.

The TCI is a 16MB pretty-printed (2-space, literal-UTF-8) JSON artifact; this transform
loads → mutates ONLY the targeted keys → dumps with the identical serializer, so untouched
entries are byte-stable and the git diff is confined to the intended lines. It never touches
any COUNTED value (row_count sums, slice sizes) — only metadata/pointer/param-name accuracy —
so it is safe to apply without re-running the Ω1 sanity gate (γ proxy ruling).
"""
import json
import sys
from pathlib import Path

TCI = Path(__file__).resolve().parents[3] / \
    "00_ARCHITECTURE/llm_consumption_audit/capability_map/TOTAL_CONCEPT_INVENTORY_v1_0.json"

CMN2_CONCEPT = "l2.contradiction_pole.domain_promise_vs_denial"


def main() -> int:
    d = json.loads(TCI.read_text(encoding="utf-8"))
    entries = d["entries"]

    before = {
        "ganita_chart_facts_get_total": 0,
        "with_fact_category_key": 0,
        "with_category_key": 0,
        "mechanism_class_entries": 0,
        "mechanism_class_already_flagged": 0,
        "cmn2_serving_tool": None,
    }
    after = dict.fromkeys(before, 0)

    n_omega8 = n_cmn1 = n_cmn2 = 0

    for e in entries:
        tool = e.get("serving_tool")
        sa = e.get("serving_args")

        # ---- Ω8-fixup: fact_category -> category on ganita_chart_facts_get ----
        if tool == "ganita_chart_facts_get":
            before["ganita_chart_facts_get_total"] += 1
            if isinstance(sa, dict) and "fact_category" in sa:
                before["with_fact_category_key"] += 1
                # rebuild dict preserving key ORDER, renaming the one key in place
                e["serving_args"] = {
                    ("category" if k == "fact_category" else k): v
                    for k, v in sa.items()
                }
                n_omega8 += 1
            elif isinstance(sa, dict) and "category" in sa:
                before["with_category_key"] += 1

        # ---- CMN-1: annotate ayanamsha-summed mechanism-class rows ----
        if tool == "bodha_mechanisms_get" and \
                (e.get("source_axis") or "").startswith("L2:bodha_mechanisms"):
            before["mechanism_class_entries"] += 1
            if e.get("is_ayanamsha_summed") is True:
                before["mechanism_class_already_flagged"] += 1
            e["is_ayanamsha_summed"] = True
            e["ayanamsha_sum_note"] = (
                "row_count_per_canonical_chart is SUMMED across all 5 ayanamshas; the live "
                "bodha_mechanisms_get defaults to one (lahiri) — divide by ~5 for the "
                "per-ayanamsha servable count. Sum is correct; this flag prevents misreading it."
            )
            n_cmn1 += 1

        # ---- CMN-2: repoint contradiction-pole serving_tool/args ----
        if e.get("concept_id") == CMN2_CONCEPT:
            before["cmn2_serving_tool"] = tool
            tclass = (sa or {}).get("tension_class")
            e["serving_tool"] = "bodha_graph_subgraph_get"
            e["serving_args"] = {
                "chart_id": (sa or {}).get("chart_id", "<chart_id>"),
                "mode": "contradictions",
                "tension_class": tclass,
            }
            e["serving_tool_fixup_note"] = (
                "CMN-2 (Ω8): was bodha_quality_get (a scorecard summary that does NOT serve the "
                "pole rows); repointed to bodha_graph_subgraph_get mode=contradictions, the surface "
                "that serves the contradiction poles + tension_class + participant signals (Ω6)."
            )
            n_cmn2 += 1

    # ---- recount after ----
    for e in entries:
        tool = e.get("serving_tool")
        sa = e.get("serving_args")
        if tool == "ganita_chart_facts_get":
            after["ganita_chart_facts_get_total"] += 1
            if isinstance(sa, dict) and "fact_category" in sa:
                after["with_fact_category_key"] += 1
            if isinstance(sa, dict) and "category" in sa:
                after["with_category_key"] += 1
        if tool == "bodha_mechanisms_get" and \
                (e.get("source_axis") or "").startswith("L2:bodha_mechanisms"):
            after["mechanism_class_entries"] += 1
            if e.get("is_ayanamsha_summed") is True:
                after["mechanism_class_already_flagged"] += 1
        if e.get("concept_id") == CMN2_CONCEPT:
            after["cmn2_serving_tool"] = tool

    TCI.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    report = {
        "edits_applied": {"omega8_fact_category_renamed": n_omega8,
                          "cmn1_mechanism_flagged": n_cmn1,
                          "cmn2_repointed": n_cmn2},
        "before": before,
        "after": after,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # ---- assertions (fail loudly) ----
    assert after["with_fact_category_key"] == 0, "Ω8-fixup incomplete: fact_category keys remain"
    assert after["with_category_key"] == before["ganita_chart_facts_get_total"], \
        "Ω8-fixup count mismatch: category keys != total ganita_chart_facts_get entries"
    assert after["mechanism_class_already_flagged"] == before["mechanism_class_entries"], \
        "CMN-1 incomplete: not all mechanism-class entries flagged"
    assert after["cmn2_serving_tool"] == "bodha_graph_subgraph_get", "CMN-2 repoint failed"
    print("\nALL ASSERTIONS PASSED", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
