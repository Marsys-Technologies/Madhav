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
    ("the required levels forget AD (an L1 without AD rows is accepted)", MIG, "levels(l) AS (VALUES (1), (2), (3)),", "levels(l) AS (VALUES (1), (3)),"),
    ("a duplicate natural-key fact is no longer a violation", MIG, "WHERE f.n > 1", "WHERE f.n > 99"),
    ("a gap inside a level is no longer a violation", MIG, "FROM d WHERE d.prev_end IS NOT NULL AND d.start_iso > d.prev_end", "FROM d WHERE d.prev_end IS NOT NULL AND false"),
    ("the horizon END edge is no longer checked", MIG, "FROM d GROUP BY d.level_n HAVING max(d.end_iso) < upper(p_horizon)", "FROM d GROUP BY d.level_n HAVING false"),
    ("the capture trigger no longer asserts the required scope", MIG, "  IF req IS NOT NULL THEN\n    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): the required population", "  IF false THEN\n    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): the required population"),
    ("a different lord at the same ordinal reads as a move again", K + "staleness.py",
     "                            and (x.get(\"content\") or {}).get(\"lord_graha\") == (e.get(\"content\") or {}).get(\"lord_graha\")\n", ""),
    ("the Python checker ignores the required members and coverage", K + "inventory_verifier.py", "    if require_contract:\n        eligible", "    if False:\n        eligible"),
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


def _run(extra=()):
    """One pytest run of the suite; returns (exit code, combined output). `-rfE` prints a FAILED/ERROR line per failing test so the outcome can be CLASSIFIED."""
    r = subprocess.run([sys.executable, "-m", "pytest", TEST, "-q", "-p", "no:cacheprovider", "-rfEs", *extra], cwd="python-sidecar",
                       capture_output=True, text=True, timeout=1800)
    return r.returncode, r.stdout + r.stderr


def classify(code: int, out: str) -> str:
    """CAUGHT only when pytest ran the tests (exit 1) and at least one test FAILED on an assertion; everything else is NOT evidence of detection:
    COLLECTION (exit 2 / collection errors / no tests ran), SETUP-ERROR (fixture or migration apply broke: an ERROR with no FAILED), SKIPPED (a required database was
    unavailable), USAGE/INTERNAL (other exit codes). A passing run is SURVIVED."""
    failed = [ln for ln in out.splitlines() if ln.startswith("FAILED ")]
    errors = [ln for ln in out.splitlines() if ln.startswith("ERROR ")]
    if code == 0:
        return "SURVIVED"
    if code == 1 and failed:
        return "CAUGHT"
    if code == 2 or "no tests ran" in out or any("collecting" in ln for ln in errors):
        return "COLLECTION-FAILURE"
    if code == 1 and errors:
        return "SETUP-ERROR"
    return f"INFRASTRUCTURE(exit {code})"


def main() -> int:
    if "--list" in sys.argv:
        for name, f, _o, _n in MUTATIONS:
            print(f"{name}  [{f}]")
        return 0
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None        # run just the mutations whose name contains this text
    # a PASSING BASELINE is required: a harness that cannot show the unmutated suite green (all selected tests passed, none skipped) proves nothing about a mutation
    code, out = _run()
    last = [ln for ln in out.splitlines() if " passed" in ln or " failed" in ln]
    if code != 0 or " skipped" in (last[-1] if last else "") or " passed" not in (last[-1] if last else ""):
        print(f"BASELINE NOT GREEN (exit {code}): {last[-1] if last else out[-300:]!r} — no mutation is meaningful; refusing to run")
        return 2
    print(f"BASELINE green: {last[-1]}")
    survivors = []
    ran = [m for m in MUTATIONS if not only or only in m[0]]
    for name, path, old, new in ran:
        text = open(path, encoding="utf-8").read()                  # path is relative to platform/ (this script's cwd)
        if old not in text:
            print(f"TARGET MISSING: {name} ({path})")
            survivors.append(name)
            continue
        try:
            open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
            code, out = _run(("-x",))
        finally:
            open(path, "w", encoding="utf-8").write(text)
        verdict = classify(code, out)
        print(f"{verdict:<20} {name}")
        if verdict != "CAUGHT":
            survivors.append(name)
    print(f"{len(ran) - len(survivors)}/{len(ran)} caught")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
