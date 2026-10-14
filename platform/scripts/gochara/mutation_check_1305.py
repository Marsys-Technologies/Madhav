#!/usr/bin/env python3
"""Reproducible mutation evidence for migration 1305 and the G12 kernel changes (the same discipline as mutation_check_1206.py).

Neuters ONE guard at a time (in the migration or in the sidecar code), runs the WHOLE G12 live suite (tests/l3/gochara/test_g12_snapshot_copy.py) against a
THROWAWAY database server, and requires every mutation to be caught by an ASSERTION of a test that ran. Files are restored in a `finally` block. It REWRITES
REPOSITORY FILES IN PLACE while it runs: run it only in a checkout of your own that nothing else is using.

Classification (see `classify`): only an ASSERTION failure of a test's call phase counts as CAUGHT (AssertionError, a rewritten `assert`, pytest's `Failed:` such as
DID NOT RAISE or an explicit pytest.fail). A call-phase failure of another exception type (a database error, PermissionError, TypeError ...) is
UNEXPECTED-EXCEPTION; a mutant that merely breaks the world's SETUP (the migration's own post-apply check refuses, or the fixture cannot build through the writer)
is SETUP-ERROR; both count as NOT caught: they prove the code defends itself, not that a test detects the behaviour. The suite's own helper
`_answers_from_the_copy` converts ONLY an explicitly identified forbidden live read into an assertion (round 6, R4); everything else propagates to here.

The list follows the round-6 structure of the migration: the capture trigger (what is validated is what is stored), the pure contract over a copy
(`ka_gochara_search_copy_violations`), identity and digests, what runs after capture (tier is metadata, drift, the stored copy recomputes), and the kernel.

NOT in the list, on purpose:
  * "the writer submits no keys": the fixtures themselves build through the writer, so the mutant breaks setup and nothing is left to assert.
  * skipping the writer's capture-time Python call (`validate_consumed_dasha_population(against_live=True)` in the snapshot substep) SURVIVES in this suite: the
    same defects are refused earlier and independently by the daśā read (`dasha_builds_mixed`, `dasha_build_not_pinned`) and by the database trigger. The
    FUNCTION is covered (its mutants are in the list); the CALL is a third, independent derivation (defence in depth) and no claim is made that a test
    isolates it.
  * the 1206 legacy branch of the completeness function (unchanged text; mutation_check_1206.py covers it).

Exit status is non-zero if any mutation is not CAUGHT or a target string is missing.

    GOCHARA_A53_ADMIN_DSN=<the admin DSN of a local THROWAWAY server> GOCHARA_A53_REQUIRE_DB=1 SE_EPHE_PATH=<se1 dir> \\
      python3 scripts/gochara/mutation_check_1305.py [--list] [--only <text>] [--slice i/n]

Run from the platform/ directory.
"""
import subprocess
import sys

MIG = "migrations/1305_gochara_snapshot_owns_l1_copy.sql"
K = "python-sidecar/services/gochara_kernel/"
TEST = "tests/l3/gochara/test_g12_snapshot_copy.py"

# (name, file, old, new)
MUTATIONS = [
    # ── the capture trigger: what is validated is what is stored (R1), one upstream snapshot, the whole upstream scope ──────────────────────────────────────
    ("the trigger keeps the SUBMITTED copy instead of the one it built", MIG,
     "SELECT public.ka_gochara_search_facts_copy(NEW.chart_id, NEW.consumed_fact_ids), public.ka_gochara_search_dasha_copy(NEW.chart_id, NEW.consumed_dasha_row_ids),",
     "SELECT COALESCE(NEW.consumed_fact_rows, public.ka_gochara_search_facts_copy(NEW.chart_id, NEW.consumed_fact_ids)), COALESCE(NEW.consumed_dasha_rows, public.ka_gochara_search_dasha_copy(NEW.chart_id, NEW.consumed_dasha_row_ids)),"),
    ("the trigger accepts an identity digest that does not recompute", MIG,
     "  IF NEW.l1_facts_digest IS DISTINCT FROM public.ka_gochara_search_copy_digest(NEW.consumed_fact_rows, 'content')\n     OR NEW.dasha_digest IS DISTINCT FROM public.ka_gochara_search_copy_digest(NEW.consumed_dasha_rows, 'content') THEN",
     "  IF false THEN"),
    ("the trigger never applies the contract to the copy it stores", MIG,
     "FROM public.ka_gochara_search_copy_violations(NEW.consumed_fact_rows, NEW.consumed_dasha_rows, hz, true) c",
     "FROM public.ka_gochara_search_copy_violations(NEW.consumed_fact_rows, NEW.consumed_dasha_rows, hz, true) c WHERE false"),
    ("the trigger judges the copy WITHOUT eligibility (the copy's own tier and build are not asserted)", MIG,
     "FROM public.ka_gochara_search_copy_violations(NEW.consumed_fact_rows, NEW.consumed_dasha_rows, hz, true) c",
     "FROM public.ka_gochara_search_copy_violations(NEW.consumed_fact_rows, NEW.consumed_dasha_rows, hz, false) c"),
    ("the trigger never compares the fact copy with the whole upstream scope", MIG,
     "FROM public.ka_gochara_search_copy_difference(NEW.consumed_fact_rows, upstream_facts) c", "FROM public.ka_gochara_search_copy_difference(NEW.consumed_fact_rows, upstream_facts) c WHERE false"),
    ("the trigger never compares the daśā copy with the whole upstream scope", MIG,
     "FROM public.ka_gochara_search_copy_difference(NEW.consumed_dasha_rows, upstream_dashas) c) u) v;", "FROM public.ka_gochara_search_copy_difference(NEW.consumed_dasha_rows, upstream_dashas) c WHERE false) u) v;"),
    # ── the contract over a copy ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    ("a child whose parent_row_id is not the row the copy holds at its parent's key is no longer a violation (the round-5 substitution)", MIG,
     "FROM kin c WHERE c.parents > 0 AND c.parents_by_id = 0", "FROM kin c WHERE c.parents > 0 AND c.parents_by_id = 0 AND false"),
    ("an orphan or wrong-level parent is no longer a violation", MIG, "FROM kin c WHERE c.parents = 0", "FROM kin c WHERE c.parents = 0 AND false"),
    ("a child outside its parent is no longer a violation", MIG, "FROM kin c WHERE c.parents > 0 AND c.parents_not_containing > 0", "FROM kin c WHERE c.parents > 0 AND false"),
    ("a lord path that is not the parent's plus the row's lord is no longer a violation", MIG, "FROM kin c WHERE c.parents > 0 AND c.parents_on_path = 0", "FROM kin c WHERE c.parents > 0 AND false"),
    ("a Mahādaśā that carries a parent is no longer a violation", MIG, "FROM d WHERE d.lv = 1 AND (d.pid IS NOT NULL OR d.plv IS NOT NULL OR d.pst IS NOT NULL);", "FROM d WHERE d.lv = 1 AND false;"),
    ("the Python checker lets a Mahādaśā carry a parent", K + "inventory_verifier.py", "            if c[\"pid\"] is not None or c[\"plv\"] is not None or c[\"pst\"] is not None:", "            if False:"),
    ("the copy's own tier is no longer asserted", MIG, "FROM dall a WHERE p_eligibility AND a.tier IS DISTINCT FROM 'two_pass_verified'", "FROM dall a WHERE p_eligibility AND false"),
    ("a copy of several builds is no longer a violation", MIG, "FROM dall a WHERE p_eligibility AND a.build IS NOT NULL HAVING count(DISTINCT a.build) > 1", "FROM dall a WHERE p_eligibility AND a.build IS NOT NULL HAVING false"),
    ("the required levels forget AD (a copy without AD rows is accepted)", MIG, "levels(l) AS (VALUES (1), (2), (3)),", "levels(l) AS (VALUES (1), (3)),"),
    ("a duplicate natural-key fact is no longer a violation", MIG, "FROM fcount c WHERE c.n > 1", "FROM fcount c WHERE c.n > 99"),
    ("a fact outside the contract may sit in the copy", MIG, "FROM f WHERE NOT f.in_scope", "FROM f WHERE NOT f.in_scope AND false"),
    ("a gap inside a level is no longer a violation", MIG, "FROM d WHERE d.prev_end IS NOT NULL AND d.st > d.prev_end", "FROM d WHERE d.prev_end IS NOT NULL AND false"),
    ("an overlap at distinct starts is no longer a violation", MIG, "FROM d WHERE d.prev_start IS NOT NULL AND d.st > d.prev_start AND d.st < d.prev_end", "FROM d WHERE d.prev_start IS NOT NULL AND false"),
    ("the horizon END edge is no longer checked", MIG, "FROM d GROUP BY d.lv HAVING max(d.en) < upper(p_horizon)", "FROM d GROUP BY d.lv HAVING false"),
    ("a period wholly outside the horizon may sit in the copy", MIG, "FROM dscope a WHERE a.in_scope AND NOT a.in_horizon", "FROM dscope a WHERE a.in_scope AND false"),
    # ── identity and digests (R3, R10) ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    ("the ordinal path is part of the identity again (a period outside the horizon changes it)", MIG,
     "'parent_start_iso', p.start_iso, 'lord_path', public.ka_gochara_search_dasha_path(p_chart, d.dasha_row_id)),",
     "'parent_start_iso', p.start_iso, 'lord_path', public.ka_gochara_search_dasha_path(p_chart, d.dasha_row_id), 'ordinal_path', public.ka_gochara_search_dasha_ordinal_path(p_chart, d.dasha_row_id)),"),
    ("the copy digest ignores which block it is asked for", MIG,
     "CASE WHEN jsonb_typeof(e.value -> p_block) = 'object'\n                      THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> p_block)) ELSE 'MISSING' END AS line",
     "CASE WHEN jsonb_typeof(e.value -> 'content') = 'object'\n                      THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> 'content')) ELSE 'MISSING' END AS line"),
    ("the copy digest orders by the key only again (conflicting duplicates in arrival order)", MIG,
     "SELECT string_agg(l.line, E'\\n' ORDER BY l.line COLLATE \"C\")", "SELECT string_agg(l.line, E'\\n' ORDER BY split_part(l.line, '|', 1) COLLATE \"C\")"),
    ("numbers inside the copy are no longer normalised", MIG,
     "IF jsonb_typeof(j) = 'number' THEN RETURN to_jsonb(trim_scale((j #>> '{}')::numeric)); END IF;",
     "IF jsonb_typeof(j) = 'number' THEN RETURN j; END IF;"),
    ("the copied ancestry accepts a parent of another ayanamsha or system", MIG, "    AND p.ayanamsha_id IS NOT DISTINCT FROM d.ayanamsha_id AND p.system_id IS NOT DISTINCT FROM d.system_id        -- a parent of another ayanamsha/system never enters the copied ancestry\n", ""),
    # ── after capture: tier is metadata (R2), drift, the stored copy recomputes (R7) ──────────────────────────────────────────────────────────────────────────
    ("the upstream scope filters on the consumed TIER again (an extra row of another tier is invisible)", MIG,
     "    WHERE d.chart_id = p_chart AND d.ayanamsha_id = 'lahiri_chitrapaksha' AND d.system_id = 'vimshottari' AND d.level_n IN (1, 2, 3)\n      AND d.start_iso < upper(p_horizon) AND d.end_iso > lower(p_horizon)) s;",
     "    WHERE d.chart_id = p_chart AND d.ayanamsha_id = 'lahiri_chitrapaksha' AND d.system_id = 'vimshottari' AND d.level_n IN (1, 2, 3)\n      AND d.verification_pass_status = 'two_pass_verified' AND d.start_iso < upper(p_horizon) AND d.end_iso > lower(p_horizon)) s;"),
    ("the drift check judges the upstream scope WITH eligibility (a tier-only change closes the gate)", MIG, "FROM public.ka_gochara_search_copy_violations(up_f, up_d, hz, false) v;", "FROM public.ka_gochara_search_copy_violations(up_f, up_d, hz, true) v;"),
    ("the dasha drift check never fires", MIG, "IF public.ka_gochara_search_copy_digest(up_d, 'content') IS DISTINCT FROM snap.dasha_digest THEN", "IF public.ka_gochara_search_copy_digest(up_d, 'content') IS DISTINCT FROM snap.dasha_digest AND false THEN"),
    ("the fact drift check never fires", MIG, "IF public.ka_gochara_search_copy_digest(up_f, 'content') IS DISTINCT FROM snap.l1_facts_digest THEN", "IF public.ka_gochara_search_copy_digest(up_f, 'content') IS DISTINCT FROM snap.l1_facts_digest AND false THEN"),
    ("the structural violations of the upstream scope are no longer reported at drift", MIG, "FROM public.ka_gochara_search_copy_violations(up_f, up_d, hz, false) v;", "FROM public.ka_gochara_search_copy_violations(up_f, up_d, hz, false) v WHERE false;"),
    ("a stored copy that does not recompute to its stored digests is no longer a violation", MIG, ") AS x(bad, d) WHERE x.bad;", ") AS x(bad, d) WHERE x.bad AND false;"),
    ("a stored copy that violates the capture contract is no longer a violation", MIG,
     "FROM public.ka_gochara_search_copy_violations(snap.consumed_fact_rows, snap.consumed_dasha_rows, hz, true) v;",
     "FROM public.ka_gochara_search_copy_violations(snap.consumed_fact_rows, snap.consumed_dasha_rows, hz, true) v WHERE false;"),
    ("the Moon-resolved domain reads live chart_dashas again (the word the presence check looks for stays in a comment)", MIG,
     "COALESCE(s.consumed_dasha_rows, public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids))",
     "COALESCE(NULL::jsonb /* consumed_dasha_rows */, public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids))"),
    ("a legacy snapshot is no longer refused at first seal by the database gate", MIG,
     "'input_snapshot_without_copy'::text", "'input_snapshot_drift'::text"),
    ("the gate no longer refuses after G8's 1306", MIG,
     "UNION ALL SELECT 'g8_1306_applied_first',", "UNION ALL SELECT 'g8_1306_not_checked',"),
    # ── the kernel ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
    ("the P1 anchor SQL names live chart_dashas for a snapshot that has a copy", K + "record_verifier.py",
     "sql = _SQL_COPY if (has_copy is not None and _scalar(has_copy) is True) else _SQL_LEGACY", "sql = _SQL_LEGACY"),
    ("an exact Decimal comparison is context-rounded again", K + "targets.py",
     "    if Decimal(repr(lam)) != exact:", "    if Decimal(repr(lam)) != exact.normalize():"),
    ("the Python checker ignores the parent row id (the substitution)", K + "inventory_verifier.py",
     "        if c[\"pid\"] is None or not any(p[\"id\"] == c[\"pid\"] for p in parents):", "        if False:"),
    ("the Python checker ignores the copy's own tier and build", K + "inventory_verifier.py", "    if eligibility:\n        for p in periods:", "    if False:\n        for p in periods:"),
    ("the Python checker ignores gaps", K + "inventory_verifier.py", "            if nxt[\"st\"] > prev[\"en\"]:", "            if False:"),
    ("the natal chart is read from a fact copy that violates the contract", K + "inventory_verifier.py",
     "    if problems:                                   # a duplicated, foreign or valueless subject is refused by name, never resolved by element order", "    if False:"),
    ("the capture-time Python check no longer requires the stored copy to hold every upstream row", K + "inventory_verifier.py",
     "        for rid in sorted(set(theirs) - set(mine)):", "        for rid in []:"),
    ("the natal chart is read from live L1 again", K + "inventory_verifier.py",
     "    if snap[\"facts\"] is None:\n        return read_chart(conn, snap[\"fact_ids\"])\n    return chart_from_copy(snap[\"facts\"])",
     "    return read_chart(conn, snap[\"fact_ids\"])"),
    ("a move ignores the full lord path (ancestry) again", K + "staleness.py", "                            and (x.get(\"content\") or {}).get(\"lord_path\") == (e.get(\"content\") or {}).get(\"lord_path\")             # the FULL ancestry (parents' lords), not only the leaf\n", ""),
    ("movement naming looks for the ordinal path in the identity block again", K + "staleness.py",
     "                    ordinal = (e.get(\"metadata\") or {}).get(\"ordinal_path\")", "                    ordinal = (e.get(\"content\") or {}).get(\"ordinal_path\")"),
    ("metadata-only drift counts as hard", K + "staleness.py", '"kind": "soft"}', '"kind": "hard"}'),
    ("staleness says self_contained for a copy that does not recompute", K + "staleness.py", '"self_contained": not inconsistencies,', '"self_contained": True,'),
    ("an inconsistent copy is not a hard component of the staleness report", K + "staleness.py",
     '"copy": {"stored": stored_input, "live": None, "same": not inconsistencies, "kind": "hard"},', '"copy": {"stored": stored_input, "live": None, "same": True, "kind": "hard"},'),
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
    if "--slice" in sys.argv:                 # --slice i/n: every n-th mutation starting at i (to spread the list over several private checkouts, one run each)
        i, n = (int(x) for x in sys.argv[sys.argv.index("--slice") + 1].split("/"))
        ran = ran[i::n]
    for name, path, old, new in ran:
        text = open(path, encoding="utf-8").read()                  # path is relative to platform/ (this script's cwd)
        if old not in text:
            print(f"TARGET MISSING: {name} ({path})")
            survivors.append(name)
            continue
        try:
            open(path, "w", encoding="utf-8").write(text.replace(old, new, 1))
            code, out, xml = _run()                       # the WHOLE suite (no -x): the report must hold every failing test so an assertion anywhere is seen
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
