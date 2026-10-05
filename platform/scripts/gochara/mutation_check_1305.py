#!/usr/bin/env python3
"""Reproducible mutation evidence for migration 1305 and the G12 kernel changes (the same discipline as mutation_check_1206.py).

Neuters ONE guard at a time (in the migration or in the sidecar code), runs the G12 live suite (tests/l3/gochara/test_g12_snapshot_copy.py) against a
THROWAWAY database server, and requires every mutation to be caught by at least one failing or erroring test. Files are restored in a `finally` block.
Mutants that only break the world's SETUP (the migration's own post-apply check refuses, or the fixture cannot build through the writer) are reported SETUP-ERROR and
count as NOT caught: they prove the migration defends itself, not that a test detects the behaviour. Mutants that were dropped for that reason or because they are
equivalent: "the writer submits no keys" (the fixtures themselves build through the writer, so nothing is left to assert), "a deleted sibling reads as a move again" (the
lord condition now masks it: two siblings of one parent never share a lord, so the mutant is behaviourally equivalent), and the two "required scope forgets a member"
variants (the writer's own capture then mismatches the shrunken population in the fixture; the required-scope function mutants below cover the same ground).

Exit status is non-zero if any mutation survives or a target string is missing.

Only an ASSERTION failure of a test that ran counts as CAUGHT (see `classify`); a mutant that merely breaks the world's SETUP (the migration's own post-apply check refuses, or the
fixture cannot build through the writer) is SETUP-ERROR and counts as NOT caught: it proves the migration defends itself, not that a test detects the behaviour. Dropped on
purpose: "the writer submits no keys" (the fixtures build through the writer, so nothing is left to assert), "a deleted sibling reads as a move again" (the lord condition now masks
it: two siblings of one parent never share a lord, so the mutant is behaviourally equivalent) and the two "required scope forgets a member" variants (the writer's own capture then
mismatches the shrunken population in the fixture; the required-scope function mutants cover the same ground).

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
    ("the dasha drift check never fires (a condition that can never be true, so the migration's own presence check still passes)", MIG,
     "           IS DISTINCT FROM snap.dasha_digest THEN", "           IS DISTINCT FROM snap.dasha_digest AND false THEN"),
    ("the Moon-resolved domain reads live chart_dashas again (the word the presence check looks for stays in a comment)", MIG,
     "COALESCE(s.consumed_dasha_rows, public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids))",
     "COALESCE(NULL::jsonb /* consumed_dasha_rows */, public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids))"),
    ("the copy digest ignores which block it is asked for", MIG,
     "CASE WHEN jsonb_typeof(e.value -> p_block) = 'object'\n                           THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> p_block))",
     "CASE WHEN jsonb_typeof(e.value -> 'content') = 'object'\n                           THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> 'content'))"),
    ("the live daśā population drops the level from the match", MIG,
     "                     AND (c.e #>> '{key,level_n}')::int = d.level_n AND (c.e #>> '{key,start_iso}')::timestamptz = d.start_iso\n                     AND c.e #>> '{key,kp_sublevel}' = COALESCE(d.kp_sublevel, ''))\n    UNION ALL",
     "                     AND (c.e #>> '{key,start_iso}')::timestamptz = d.start_iso\n                     AND c.e #>> '{key,kp_sublevel}' = COALESCE(d.kp_sublevel, ''))\n    UNION ALL"),
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
    ("the drift view selects by the copied TIER again (a tier-only change reads as a missing row)", MIG,
     "    WHERE d.chart_id = p_chart\n      AND EXISTS (SELECT 1 FROM jsonb_array_elements(COALESCE(p_copy, '[]'::jsonb)) AS c(e)",
     "    WHERE d.chart_id = p_chart AND d.verification_pass_status = 'two_pass_verified'\n      AND EXISTS (SELECT 1 FROM jsonb_array_elements(COALESCE(p_copy, '[]'::jsonb)) AS c(e)"),
    ("a legacy snapshot is no longer refused at first seal by the database gate", MIG,
     "'input_snapshot_without_copy'::text", "'input_snapshot_drift'::text"),
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
    ("a child outside its parent is no longer a violation", MIG, "WHERE c.level_n IN (2, 3) AND NOT (c.start_iso >= p.start_iso AND c.end_iso <= p.end_iso)", "WHERE c.level_n IN (2, 3) AND false"),
    ("an orphan or wrong-level parent is no longer a violation", MIG, "FROM d c WHERE c.level_n IN (2, 3)\n              AND NOT EXISTS", "FROM d c WHERE c.level_n IN (2, 3) AND false\n              AND NOT EXISTS"),
    ("the drift check judges the required scope by the consumed TIER again (a tier-only change closes the gate)", MIG, "snap.consumed_dasha_rows) v;", "NULL::jsonb) v;"),
    ("a move ignores the full lord path (ancestry) again", K + "staleness.py", "                            and (x.get(\"content\") or {}).get(\"lord_path\") == (e.get(\"content\") or {}).get(\"lord_path\")             # the FULL ancestry (parents' lords), not only the leaf\n", ""),
    ("the copied ancestry accepts a parent of another ayanamsha or system", MIG, "    AND p.ayanamsha_id IS NOT DISTINCT FROM d.ayanamsha_id AND p.system_id IS NOT DISTINCT FROM d.system_id        -- a parent of another ayanamsha/system never enters the copied ancestry\n", ""),
    ("the Python checker ignores the hierarchy", K + "inventory_verifier.py", "            if par is None or int(par[\"level_n\"]) != level - 1", "            if False and par is None or int(par[\"level_n\"]) != level - 1"),
    ("numbers inside the copy are no longer normalised", MIG,
     "IF jsonb_typeof(j) = 'number' THEN RETURN to_jsonb(trim_scale((j #>> '{}')::numeric)); END IF;",
     "IF jsonb_typeof(j) = 'number' THEN RETURN j; END IF;"),
    ("the gate no longer refuses after G8's 1306", MIG,
     "UNION ALL SELECT 'g8_1306_applied_first',", "UNION ALL SELECT 'g8_1306_not_checked',"),
    ("metadata-only drift counts as hard", K + "staleness.py", '"kind": "soft"}', '"kind": "hard"}'),
    ("the natal chart is read from live L1 again", K + "inventory_verifier.py",
     "    if snap[\"facts\"] is None:\n        return read_chart(conn, snap[\"fact_ids\"])\n    return chart_from_copy(snap[\"facts\"])",
     "    return read_chart(conn, snap[\"fact_ids\"])"),
]


def _run(extra=()):
    """One pytest run of the suite; returns (exit code, combined output, junit XML text or None). The XML is the STRUCTURED report `classify` reads."""
    import os
    import tempfile
    fd, xml_path = tempfile.mkstemp(suffix=".xml")
    os.close(fd)
    try:
        r = subprocess.run([sys.executable, "-m", "pytest", TEST, "-q", "-p", "no:cacheprovider", "-rfEs", f"--junitxml={xml_path}", *extra], cwd="python-sidecar",
                           capture_output=True, text=True, timeout=1800)
        xml = open(xml_path, encoding="utf-8").read() if os.path.getsize(xml_path) else None
    finally:
        os.unlink(xml_path)
    return r.returncode, r.stdout + r.stderr, xml


def classify(code: int, out: str, xml: str | None = None) -> str:
    """Classify a pytest run from its STRUCTURED report (junit XML), not from text (Codex G12 round 4, item 5: `FAILED ... - psycopg.OperationalError: connection lost` used to read as
    CAUGHT). CAUGHT only when a test's CALL phase failed on an ASSERTION (AssertionError, a pytest `Failed:` such as DID NOT RAISE, or a rewritten `assert ...`). Everything else
    is NOT evidence of detection: UNEXPECTED-EXCEPTION (a call-phase failure with another exception type: a database error, PermissionError, TypeError...), SETUP-ERROR
    (a fixture/setup/teardown error), COLLECTION-FAILURE, INFRASTRUCTURE (no readable report, other exits). A passing run is SURVIVED."""
    import xml.etree.ElementTree as ET
    if code == 0:
        return "SURVIVED"
    if not xml:
        return f"INFRASTRUCTURE(exit {code}, no report)"
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return f"INFRASTRUCTURE(exit {code}, unreadable report)"
    assertion, other_call, setup, collection = 0, 0, 0, 0
    for case in root.iter("testcase"):
        for el in case.findall("failure"):
            msg = (el.get("message") or "").strip()
            if msg.startswith(("assert ", "AssertionError", "Failed:")) or "DID NOT RAISE" in msg:
                assertion += 1
            else:
                other_call += 1
        for el in case.findall("error"):
            if "collection failure" in (el.get("message") or ""):
                collection += 1
            else:
                setup += 1
    if assertion:
        return "CAUGHT"
    if collection or not any(True for _ in root.iter("testcase")):
        return "COLLECTION-FAILURE"
    if other_call:
        return "UNEXPECTED-EXCEPTION"
    if setup:
        return "SETUP-ERROR"
    return f"INFRASTRUCTURE(exit {code})"


def main() -> int:
    if "--list" in sys.argv:
        for name, f, _o, _n in MUTATIONS:
            print(f"{name}  [{f}]")
        return 0
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None        # run just the mutations whose name contains this text
    # a PASSING BASELINE is required: a harness that cannot show the unmutated suite green (all selected tests passed, none skipped) proves nothing about a mutation
    code, out, xml = _run()
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
            code, out, xml = _run(("-x",))
        finally:
            open(path, "w", encoding="utf-8").write(text)
        verdict = classify(code, out, xml)
        print(f"{verdict:<20} {name}")
        if verdict != "CAUGHT":
            survivors.append(name)
    print(f"{len(ran) - len(survivors)}/{len(ran)} caught")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
