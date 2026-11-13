"""Pure cross-ayanamsha fragility assessment of persisted Gestalt rows."""
from __future__ import annotations

import json


def assess_fragility_rows(rows: list[dict]) -> dict:
    """Assess the rows read for one chart/build, in their original order."""
    # The number of distinct ayanamshas whose gestalt row this build really wrote
    # (a count of rows read back, not the size of the canonical list).
    ayanamsha_count = len({r["ayanamsha_id"] for r in rows})

    if len(rows) < 2:
        return {
            "fragility_class": None,
            "terms": {"ayanamsha_rows_compared": len(rows)},
            "error": None,
            "ayanamsha_count": ayanamsha_count,
        }

    # domain -> {ayanamsha_id -> dominant_valence}
    per_domain: dict[str, dict[str, str]] = {}
    for r in rows:
        aya = r["ayanamsha_id"]
        vm = r["domain_verdict_map_jsonb"]
        if isinstance(vm, str):
            vm = json.loads(vm)
        for domain, entry in (vm or {}).items():
            ev = (entry or {}).get("evidence", {})
            b = int(ev.get("benefic_count") or 0)
            m = int(ev.get("malefic_count") or 0)
            dominant = "benefic_leaning" if b > m else "malefic_leaning" if m > b else "balanced"
            per_domain.setdefault(domain, {})[aya] = dominant

    compared_domains = []
    disagreeing_domains = []
    for domain, by_aya in per_domain.items():
        if len(by_aya) < 2:
            continue  # this domain didn't appear in enough rows to compare
        compared_domains.append(domain)
        if len(set(by_aya.values())) > 1:
            disagreeing_domains.append(domain)

    if not compared_domains:
        return {
            "fragility_class": None,
            "terms": {"ayanamsha_rows_compared": len(rows), "domains_compared": 0},
            "error": None,
            "ayanamsha_count": ayanamsha_count,
        }

    fragility_class = "ayanamsha_sensitive" if disagreeing_domains else "stable_across_ayanamsha"
    return {
        "fragility_class": fragility_class,
        "terms": {
            "ayanamsha_rows_compared": len(rows),
            "domains_compared": sorted(compared_domains),
            "domains_disagreeing": sorted(disagreeing_domains),
        },
        "error": None,
        "ayanamsha_count": ayanamsha_count,
    }
