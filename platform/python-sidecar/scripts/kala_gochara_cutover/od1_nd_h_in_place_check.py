"""SR-SOLVER-PLAN-1 / SR-OD1 V1 — the MEASURED check behind re-deriving the ND-H 1.2.0 rows IN PLACE.

SR-SOLVER-PLAN-1: new rule versions for everything that changes semantics; in-place re-derivation only for
decision-pending rules, conditioned on a measured check that no sealed generation references them. The 1.2.0 rows
(P1/P3/P4 of the eight ND-H classes and bereavement's P3/P4) took their soft factors from the 1.0.0 rows; V1 moves
them to the 1.3.0 doctrine rows. That is a legitimate edit only if no durable generation holds a 1.2.0 row — a
sealed row is never edited (§N.4, "surgical migrations").

What this script measures (all read-only; it never opens a database):

  1. SEEDING PATHS — the only code that writes registry rows is `RuleRegistryStore.seed()` over `bound_path_refs()`.
     Under the MEASURING (legacy) profile that catalogue must hold no 1.2.0 row, and no migration may INSERT one into a
     gochara registry / record table. (A migration that merely READS 1.2.0, e.g. the 1381 near-miss detector, is not
     a seed.)
  2. THE SAVED MEASURING GOLDEN — the only durable production generation with data — carries rule_version 1.0.0 only
     (records carry it inside `gkey`, windows as a column).
  3. THE QUERIES the cockpit runs against any database the generation may live in (this job may not connect to one):
     zero rows everywhere ⇒ in-place; any row ⇒ the 3-day fork (a new 1.4.0 and the literal sites generalised).

Exit 0 ⇒ nothing measured references 1.2.0 in a durable generation. Run: `python3 -I <this file> [golden_dir]`.
"""
from __future__ import annotations

import collections
import json
import os
import re
import sys
from pathlib import Path

ND_H_VERSION = "1.2.0"
_REPO = Path(__file__).resolve().parents[4]
_GOLDEN = Path("/Users/Dev/kalayantra/measuring-golden-20261018/golden")

#: run by the cockpit, read-only, on every database a generation may live in (production included)
DB_QUERIES = (
    "SELECT generation, rule_version, count(*) FROM public.ka_gochara_relationship_record"
    " WHERE rule_version = '1.2.0' GROUP BY 1, 2",
    "SELECT generation, rule_version, count(*) FROM public.ka_gochara_eval_window"
    " WHERE rule_version = '1.2.0' GROUP BY 1, 2",
    "SELECT generation, rule_version, count(*) FROM public.ka_gochara_search_path_pin"
    " WHERE rule_version = '1.2.0' GROUP BY 1, 2",
    "SELECT path_id, rule_version FROM public.ka_gochara_rule_path_seal WHERE rule_version = '1.2.0'",
)

_INSERT_RE = re.compile(r"INSERT\s+INTO\s+(?:public\.)?(ka_gochara_\w+)(.*?);", re.I | re.S)


def seeding_migrations(repo: Path = _REPO) -> list[str]:
    """Migrations that INSERT a '1.2.0' value into a gochara table (a seed of the rows V1 re-derives)."""
    out = []
    for sql in sorted((repo / "platform" / "migrations").glob("*.sql")):
        text = sql.read_text(errors="ignore")
        for m in _INSERT_RE.finditer(text):
            if "'1.2.0'" in m.group(2):
                out.append(f"{sql.name}: {m.group(1)}")
    return out


def legacy_profile_catalogue() -> dict:
    """What the measuring (default) profile would seed / select — read from the live registry, not restated."""
    sys.path.insert(0, str(_REPO / "platform" / "python-sidecar"))
    from services.gochara_kernel import rule_registry as rr
    refs = rr.bound_path_refs()
    selected = {cls: rr.selected_versions_for(cls) for cls in ("marriage", "business_launch", "bereavement")}
    return {"bound_path_refs": [list(r) for r in refs],
            "has_1_2_0": any(v == ND_H_VERSION for _p, v in refs),
            "selected_has_1_2_0": any(v == ND_H_VERSION for s in selected.values() for v in s.values())}


def golden_versions(golden: Path = _GOLDEN) -> dict | None:
    """rule_version counts of the saved measuring golden (None if the golden is not on this machine)."""
    if not (golden / "records.jsonl").exists():
        return None
    records, windows = collections.Counter(), collections.Counter()
    with open(golden / "records.jsonl") as fh:
        for line in fh:
            records[json.loads(json.loads(line)["gkey"])["rule_version"]] += 1
    with open(golden / "windows.jsonl") as fh:
        for line in fh:
            windows[json.loads(line)["rule_version"]] += 1
    return {"records": dict(records), "windows": dict(windows)}


def measure(golden: Path = _GOLDEN) -> dict:
    result = {"seeding_migrations": seeding_migrations(), "legacy_profile": legacy_profile_catalogue(),
              "golden": golden_versions(golden), "db_queries_for_the_cockpit": list(DB_QUERIES),
              "db_checked_here": False}
    g = result["golden"]
    result["references_1_2_0"] = bool(
        result["seeding_migrations"] or result["legacy_profile"]["has_1_2_0"]
        or result["legacy_profile"]["selected_has_1_2_0"]
        or (g and (ND_H_VERSION in g["records"] or ND_H_VERSION in g["windows"])))
    return result


if __name__ == "__main__":
    report = measure(Path(sys.argv[1]) if len(sys.argv) > 1 else _GOLDEN)
    print(json.dumps(report, indent=1, sort_keys=True))
    sys.exit(1 if report["references_1_2_0"] else 0)
