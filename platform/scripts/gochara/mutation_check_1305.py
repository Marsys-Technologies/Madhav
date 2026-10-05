#!/usr/bin/env python3
"""Reproducible mutation evidence for migration 1305 and the G12 kernel changes (the same discipline as mutation_check_1206.py).

Neuters ONE guard at a time (in the migration or in the sidecar code), runs the G12 live suite (tests/l3/gochara/test_g12_snapshot_copy.py) against a
THROWAWAY database server, and requires every mutation to be caught by at least one failing or erroring test. Files are restored in a `finally` block.
Exit status is non-zero if any mutation survives or a target string is missing.

NOT in the list, on purpose: skipping the verifier's own capture-time derivation (`validate_consumed_dasha_population(against_live=True)` in the writer's snapshot
substep) survives, because the same defects are refused earlier and independently by the daśā read (`dasha_builds_mixed`, `dasha_build_not_pinned`) and by the
database trigger (an incomplete or conflicting population). It is kept as a third, independent derivation (defence in depth), and no claim is made that a test
isolates it.

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
     "IF public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_live_population(p_chart, snap.consumed_dasha_rows,\n           (SELECT q.horizon FROM public.kala_gochara_publication q WHERE q.chart_id = p_chart AND q.generation = p_generation)), 'content')\n           IS DISTINCT FROM snap.dasha_digest THEN",
     "IF false THEN"),
    ("the copy digest ignores which block it is asked for", MIG,
     "CASE WHEN jsonb_typeof(e.value -> p_block) = 'object'\n                           THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> p_block))",
     "CASE WHEN jsonb_typeof(e.value -> 'content') = 'object'\n                           THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> 'content'))"),
    ("the live daśā population drops the level from the match", MIG,
     "                     AND (c.e #>> '{key,level_n}')::int = d.level_n AND (c.e #>> '{key,start_iso}')::timestamptz = d.start_iso\n                     AND c.e #>> '{key,kp_sublevel}' = COALESCE(d.kp_sublevel, ''))\n    UNION ALL",
     "                     AND (c.e #>> '{key,start_iso}')::timestamptz = d.start_iso\n                     AND c.e #>> '{key,kp_sublevel}' = COALESCE(d.kp_sublevel, ''))\n    UNION ALL"),
    ("the Moon-resolved domain reads live chart_dashas again", MIG,
     "COALESCE(s.consumed_dasha_rows, public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids))",
     "public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids)"),
    ("the trigger keeps the SUBMITTED copy instead of the one it built", MIG,
     "NEW.consumed_fact_rows := facts;\n  NEW.consumed_dasha_rows := dashas;",
     "NEW.consumed_fact_rows := COALESCE(NEW.consumed_fact_rows, facts);\n  NEW.consumed_dasha_rows := COALESCE(NEW.consumed_dasha_rows, dashas);"),
    ("the trigger accepts an identity digest that does not recompute", MIG,
     "IF NEW.l1_facts_digest IS DISTINCT FROM l1 OR NEW.dasha_digest IS DISTINCT FROM dd THEN", "IF false THEN"),
    ("the trigger never checks the facts are the COMPLETE live population", MIG,
     "IF public.ka_gochara_search_copy_digest(public.ka_gochara_search_facts_live_population(NEW.chart_id), 'content') IS DISTINCT FROM l1 THEN",
     "IF false THEN"),
    ("the trigger never checks the daśā rows are the COMPLETE live population", MIG,
     "IF public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_required_population(NEW.chart_id, hz), 'content') IS DISTINCT FROM dd THEN",
     "IF false THEN"),
    ("the required daśā scope forgets the AD level (a whole level can be omitted again)", MIG,
     "AND d.system_id = 'vimshottari' AND d.level_n IN (1, 2, 3)\n      AND d.verification_pass_status = 'two_pass_verified'\n      AND d.start_iso < upper(p_horizon) AND d.end_iso > lower(p_horizon)) s;",
     "AND d.system_id = 'vimshottari' AND d.level_n IN (1, 3)\n      AND d.verification_pass_status = 'two_pass_verified'\n      AND d.start_iso < upper(p_horizon) AND d.end_iso > lower(p_horizon)) s;"),
    ("the required fact scope forgets SUN (a whole subject can be omitted again)", MIG,
     "f.fact_subject IN ('LAGNA', 'SUN', 'MOON',", "f.fact_subject IN ('LAGNA', 'MOON',"),
    ("the drift view selects by the copied TIER again (a tier-only change reads as a missing row)", MIG,
     "    WHERE d.chart_id = p_chart\n      AND EXISTS (SELECT 1 FROM jsonb_array_elements(COALESCE(p_copy, '[]'::jsonb)) AS c(e)",
     "    WHERE d.chart_id = p_chart AND d.verification_pass_status = 'two_pass_verified'\n      AND EXISTS (SELECT 1 FROM jsonb_array_elements(COALESCE(p_copy, '[]'::jsonb)) AS c(e)"),
    ("a legacy snapshot is no longer refused at first seal by the database gate", MIG,
     "'input_snapshot_without_copy'::text", "'input_snapshot_drift'::text"),
    ("a deleted sibling is reported as a move again (live rows already matched can explain a missing one)", K + "staleness.py",
     "cand = [x for x in unmatched_live if id(x) not in used", "cand = [x for xs in live.values() for x in xs if id(x) not in used"),
    ("the P1 anchor SQL names live chart_dashas for a snapshot that has a copy", K + "record_verifier.py",
     "sql = _SQL_COPY if (has_copy is not None and _scalar(has_copy) is True) else _SQL_LEGACY", "sql = _SQL_LEGACY"),
    ("an exact Decimal comparison is context-rounded again", K + "targets.py",
     "    if Decimal(repr(lam)) != exact:", "    if Decimal(repr(lam)) != exact.normalize():"),
    ("numbers inside the copy are no longer normalised", MIG,
     "IF jsonb_typeof(j) = 'number' THEN RETURN to_jsonb(trim_scale((j #>> '{}')::numeric)); END IF;",
     "IF jsonb_typeof(j) = 'number' THEN RETURN j; END IF;"),
    ("the gate no longer refuses after G8's 1306", MIG,
     "UNION ALL SELECT 'g8_1306_applied_first',", "UNION ALL SELECT 'g8_1306_not_checked',"),
    ("metadata-only drift counts as hard", K + "staleness.py", '"kind": "soft"}', '"kind": "hard"}'),
    ("the writer submits no keys (nothing for the database to build the copy from)", K + "inventory_store.py",
     "if self.snapshot_copy_available():\n            # G12 (Codex round 1, ruling 2)", "if False and self.snapshot_copy_available():\n            # G12 (Codex round 1, ruling 2)"),
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
