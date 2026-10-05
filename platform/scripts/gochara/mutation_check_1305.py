#!/usr/bin/env python3
"""Reproducible mutation evidence for migration 1305 and the G12 kernel changes (the same discipline as mutation_check_1206.py).

Neuters ONE guard at a time (in the migration or in the sidecar code), runs the G12 live suite (tests/l3/gochara/test_g12_snapshot_copy.py) against a
THROWAWAY database server, and requires every mutation to be caught by at least one failing or erroring test. Files are restored in a `finally` block.
Exit status is non-zero if any mutation survives or a target string is missing.

    GOCHARA_A53_ADMIN_DSN=postgresql://postgres@127.0.0.1:5432/postgres GOCHARA_A53_REQUIRE_DB=1 SE_EPHE_PATH=<se1 dir> \\
      python3 scripts/gochara/mutation_check_1305.py [--list]

Run from the platform/ directory.
"""
import subprocess
import sys

MIG = "migrations/1305_gochara_snapshot_owns_l1_copy.sql"
K = "python-sidecar/services/gochara_kernel/"
TEST = "tests/l3/gochara/test_g12_snapshot_copy.py"

# (name, file, old, new)
MUTATIONS = [
    ("the dasha drift check never fires", MIG,
     "IF public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_live_copy(p_chart, snap.consumed_dasha_rows), 'content')\n           IS DISTINCT FROM snap.dasha_digest THEN",
     "IF false THEN"),
    ("the copy digest ignores which block it is asked for", MIG,
     "CASE WHEN jsonb_typeof(e.value -> p_block) = 'object'\n                           THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> p_block))",
     "CASE WHEN jsonb_typeof(e.value -> 'content') = 'object'\n                           THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> 'content'))"),
    ("the live daśā lookup drops the level from the natural key", MIG,
     "AND d.level_n = (k.key ->> 'level_n')::int AND d.start_iso", "AND d.start_iso"),
    ("the Moon-resolved domain reads live chart_dashas again", MIG,
     "COALESCE(s.consumed_dasha_rows, public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids))",
     "public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids)"),
    ("the copy-check trigger accepts a digest that does not recompute", MIG,
     "IF NEW.l1_facts_digest IS DISTINCT FROM public.ka_gochara_search_copy_digest(NEW.consumed_fact_rows, 'content')",
     "IF false AND NEW.l1_facts_digest IS DISTINCT FROM public.ka_gochara_search_copy_digest(NEW.consumed_fact_rows, 'content')"),
    ("the copy-check trigger accepts metadata digests that do not recompute", MIG,
     "IF NEW.l1_facts_metadata_digest IS DISTINCT FROM public.ka_gochara_search_copy_digest(NEW.consumed_fact_rows, 'metadata')",
     "IF false AND NEW.l1_facts_metadata_digest IS DISTINCT FROM public.ka_gochara_search_copy_digest(NEW.consumed_fact_rows, 'metadata')"),
    ("the gate no longer refuses after G8's 1306", MIG,
     "UNION ALL SELECT 'g8_1306_applied_first',", "UNION ALL SELECT 'g8_1306_not_checked',"),
    ("the verifier validates the population against live L1 again", K + "inventory_verifier.py",
     "if copies is not None and copies[\"dashas\"] is not None:\n        horizon = conn.execute(", "if False:\n        horizon = conn.execute("),
    ("metadata-only drift counts as hard", K + "staleness.py", '"kind": "soft"}', '"kind": "hard"}'),
    ("the writer never writes the copy", K + "inventory_store.py",
     "if self.snapshot_copy_available():\n            facts_copy", "if False and self.snapshot_copy_available():\n            facts_copy"),
    ("the natal chart is read from live L1 again", K + "inventory_verifier.py",
     "    if snap[\"facts\"] is None:\n        return read_chart(conn, snap[\"fact_ids\"])\n    return chart_from_copy(snap[\"facts\"])",
     "    return read_chart(conn, snap[\"fact_ids\"])"),
]


def main() -> int:
    if "--list" in sys.argv:
        for name, f, _o, _n in MUTATIONS:
            print(f"{name}  [{f}]")
        return 0
    survivors = []
    for name, f, old, new in MUTATIONS:
        path = f                                       # relative to platform/ (this script's cwd)
        text = open(path, encoding="utf-8").read()
        if old not in text:
            print(f"TARGET MISSING: {name} ({f})")
            survivors.append(name)
            continue
        try:
            open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
            r = subprocess.run([sys.executable, "-m", "pytest", TEST, "-q", "-x", "-p", "no:cacheprovider"], cwd="python-sidecar",
                               capture_output=True, text=True, timeout=1200)
        finally:
            open(path, "w", encoding="utf-8").write(text)
        caught = r.returncode != 0
        print(("CAUGHT  " if caught else "SURVIVED") + f" {name}")
        if not caught:
            survivors.append(name)
    print(f"{len(MUTATIONS) - len(survivors)}/{len(MUTATIONS)} caught")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
