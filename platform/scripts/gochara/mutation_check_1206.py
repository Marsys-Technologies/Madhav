#!/usr/bin/env python3
"""Reproducible mutation evidence for migration 1206 (Codex v1.0 R5).

Neuters one guard of platform/migrations/1206_gochara_search_inventory_completeness.sql at a
time, runs the live-DB suite + the static test against a THROWAWAY database, and requires that
EVERY mutation is caught by at least one failing test. The migration file is restored in a
`finally` block. Exit status is non-zero if any mutation survives or a target string is missing.

    GOCHARA_A51_TEST_DATABASE_URL=postgres://postgres@127.0.0.1:5432/gochara_a51_test \\
      python3 scripts/gochara/mutation_check_1206.py [--list]

Run from the platform/ directory.
"""
import os
import re
import subprocess
import sys

F = 'migrations/1206_gochara_search_inventory_completeness.sql'
TESTS = ['tests/integration/gochara_b6_am5_search_inventory.db.test.ts',
         'tests/unit/migrations/gochara_b6_am5_search_inventory_static.test.ts']

# (name, old, new) — each `old` must occur exactly where the guard lives
MUTATIONS = [
    ("R1 commitment equality loses the owning path/version",
     "(o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version, o.ob_id)\n                                        = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version, c)))\n       OR EXISTS",
     "(o.chart_id, o.generation, o.event_class, o.ob_id)\n                                        = (p.chart_id, p.generation, p.event_class, c)))\n       OR EXISTS"),
    ("no committed_set_mismatch at all",
     "  FROM public.ka_gochara_search_path_pin p\n  WHERE p.chart_id = p_chart AND p.generation = p_generation\n    AND ( EXISTS (SELECT 1 FROM unnest(p.committed_ob_ids) c",
     "  FROM public.ka_gochara_search_path_pin p\n  WHERE false AND p.chart_id = p_chart AND p.generation = p_generation\n    AND ( EXISTS (SELECT 1 FROM unnest(p.committed_ob_ids) c"),
    ("R2 snapshot not bound to the publication bridge (insert time)",
     "    IF bridged IS DISTINCT FROM NEW.convention_id THEN", "    IF false THEN"),
    ("R2 partition convention mismatch not checked",
     "      AND b.sky_convention_id IS DISTINCT FROM snap.convention_id;\n  END IF;", "      AND false;\n  END IF;"),
    ("R2 partition bridge-missing not checked",
     "      AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_convention_bridge b WHERE b.kala_convention_id = c.convention_id);",
     "      AND false;"),
    ("R3 NULL exclusion_reason accepted (nullable boolean reintroduced)",
     "AND exclusion_reason IS NOT NULL\n            AND COALESCE(exclusion_reason IN ('not_applicable_to_class','on_demand_tier','disabled_form',\n                                              'inputs_unavailable','tier_withheld_by_ruling','superseded_by_version'), false))",
     "AND (exclusion_reason IN ('not_applicable_to_class','on_demand_tier','disabled_form',\n                                              'inputs_unavailable','tier_withheld_by_ruling','superseded_by_version')))"),
    ("R3 ruling_ref iff degrading dropped",
     "           = (ruling_ref IS NOT NULL)),", "           = (ruling_ref IS NOT NULL) OR true),"),
    ("R4 audit column computed_at not excluded from the L1 digest",
     "to_jsonb(f) - 'computed_at'", "to_jsonb(f)"),
    ("R4 dasha digest not pinned to UTC",
     "RETURNS text LANGUAGE plpgsql STABLE\nSET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$\nDECLARE d text;\nBEGIN\n  SELECT public.ka_gochara_sha256_hex(COALESCE(string_agg(\n           i.id::text",
     "RETURNS text LANGUAGE plpgsql STABLE\nSET search_path = pg_catalog, public AS $$\nDECLARE d text;\nBEGIN\n  SELECT public.ka_gochara_sha256_hex(COALESCE(string_agg(\n           i.id::text"),
    ("ledger digest not input-bound",
     "'input=' || i.input_digest ||\n           COALESCE(", "''  ||\n           COALESCE("),
    ("no replay branch", "  IF FOUND THEN\n    -- REPLAY", "  IF FALSE THEN\n    -- REPLAY"),
    ("no L1 drift check", "IF live_l1 IS DISTINCT FROM snap.l1_facts_digest THEN", "IF false THEN"),
    ("no dasha drift check", "IF live_dasha IS DISTINCT FROM snap.dasha_digest THEN", "IF false THEN"),
    ("no obligation_uncovered", "    AND NOT isempty(i.horizon::tstzmultirange -", "    AND false AND NOT isempty(i.horizon::tstzmultirange -"),
    ("verification equality not enforced",
     "AND v.rederived_inventory_digest IS DISTINCT FROM i.inventory_digest) );\nEND;\n$$;", "AND false) );\nEND;\n$$;"),
    ("mixed-snapshot FK removed",
     "  CONSTRAINT kgsiv_input_fk FOREIGN KEY (chart_id, generation, event_class, input_digest)\n    REFERENCES public.ka_gochara_search_inventory (chart_id, generation, event_class, input_digest),\n", ""),
    ("uncommitted obligation accepted", "IF NOT (NEW.ob_id = ANY (pin.committed_ob_ids)) THEN", "IF false THEN"),
    ("seal refusal disabled",
     "IF n > 0 THEN\n    RAISE EXCEPTION 'ka_gochara_generation_seal refused (AM-5 search completeness)",
     "IF false THEN\n    RAISE EXCEPTION 'ka_gochara_generation_seal refused (AM-5 search completeness)"),
    ("no partition_overclaims", "    AND ( c.completed_horizon IS DISTINCT FROM i.horizon", "    AND false AND ( c.completed_horizon IS DISTINCT FROM i.horizon"),
    ("finalisation inventory digest not recomputed",
     "IF NEW.inventory_digest IS DISTINCT FROM public.ka_gochara_search_inventory_digest(OLD.chart_id, OLD.generation, OLD.event_class)",
     "IF false AND NEW.inventory_digest IS DISTINCT FROM public.ka_gochara_search_inventory_digest(OLD.chart_id, OLD.generation, OLD.event_class)"),
    ("finalisation ledger digest not recomputed",
     "OR NEW.ledger_digest IS DISTINCT FROM public.ka_gochara_search_ledger_digest(OLD.chart_id, OLD.generation, OLD.event_class) THEN",
     "OR false THEN"),
    ("basis excluded from the preimage", "COALESCE(p.basis, '') || '|' ||", "'' || '|' ||"),
    ("no registry accounting",
     "  CROSS JOIN public.ka_gochara_rule_path_seal rs\n  WHERE i.chart_id = p_chart AND i.generation = p_generation\n    AND NOT EXISTS",
     "  CROSS JOIN public.ka_gochara_rule_path_seal rs\n  WHERE false AND i.chart_id = p_chart AND i.generation = p_generation\n    AND NOT EXISTS"),
    ("sealed generation mutable", "IF public.ka_gochara_generation_is_sealed(ch, gen) THEN", "IF false THEN"),
    ("manifest vector not bound at insert", "    IF pub.input_generation_vector IS DISTINCT FROM NEW.input_generation_vector THEN", "    IF false THEN"),
    ("interval overlap allowed", "AND v.search_range && NEW.search_range) THEN", "AND false) THEN"),
    ("v1.2 superseded_by_version dropped from the closed reasons",
     "'inputs_unavailable','tier_withheld_by_ruling','superseded_by_version'), false))\n           OR (disposition",
     "'inputs_unavailable','tier_withheld_by_ruling'), false))\n           OR (disposition"),
    ("v1.2 superseded_by_version treated as degrading (ruling_ref demanded)",
     "COALESCE(exclusion_reason IN ('disabled_form','inputs_unavailable','tier_withheld_by_ruling'), false))",
     "COALESCE(exclusion_reason IN ('disabled_form','inputs_unavailable','tier_withheld_by_ruling','superseded_by_version'), false))"),
    ("v1.2 no multiple_included_versions seal check",
     "  HAVING count(DISTINCT p.rule_version) > 1;", "  HAVING false;"),
    ("v1.2 no superseded_without_included_version seal check",
     "    AND p.disposition = 'excluded' AND p.exclusion_reason = 'superseded_by_version'\n    AND NOT EXISTS",
     "    AND p.disposition = 'excluded' AND p.exclusion_reason = 'superseded_by_version'\n    AND false AND NOT EXISTS"),
    ("R6 builder loses EXECUTE on a digest helper (utc_ts)",
     "      public.ka_gochara_utc_ts(timestamptz),\n", ""),
    ("R6 builder loses EXECUTE on a contract function its guards call (lock_chart)",
     "      public.ka_gochara_lock_chart(uuid),\n", ""),
    ("R6 builder gains EXECUTE on the seal function",
     "      public.ka_gochara_horizon_finite_ok(tstzrange)\n      TO data_plane_builder;",
     "      public.ka_gochara_horizon_finite_ok(tstzrange), public.ka_gochara_seal_generation(uuid, text)\n      TO data_plane_builder;"),
    ("builder gets INSERT on the seal table",
     "GRANT SELECT ON public.ka_gochara_generation_seal, public.ka_gochara_av_polarity_declaration\n      TO data_plane_builder;",
     "GRANT SELECT, INSERT ON public.ka_gochara_generation_seal, public.ka_gochara_av_polarity_declaration\n      TO data_plane_builder;"),
]


def main() -> int:
    if '--list' in sys.argv:
        for i, (n, _, _) in enumerate(MUTATIONS, 1):
            print(f"{i:2d}. {n}")
        return 0
    if not os.environ.get('GOCHARA_A51_TEST_DATABASE_URL'):
        print('GOCHARA_A51_TEST_DATABASE_URL is required', file=sys.stderr)
        return 2
    src = open(F).read()
    survived, missing = [], []
    try:
        for name, old, new in MUTATIONS:
            if src.count(old) != 1:
                missing.append(f"{name} (target occurs {src.count(old)}x)")
                continue
            open(F, 'w').write(src.replace(old, new, 1))
            out = subprocess.run(['npx', 'vitest', 'run', *TESTS, '--reporter=dot'], capture_output=True, text=True,
                                 env=os.environ, timeout=600)
            text = out.stdout + out.stderr
            failed = out.returncode != 0 and re.search(r'Tests\s+.*failed', text) is not None
            print(('CAUGHT   ' if failed else 'SURVIVED ') + name, flush=True)
            if not failed:
                survived.append(name)
    finally:
        open(F, 'w').write(src)
    print(f"\n{len(MUTATIONS) - len(survived) - len(missing)}/{len(MUTATIONS)} caught; "
          f"{len(survived)} survived; {len(missing)} target(s) not found")
    for m in survived + missing:
        print('  ✗', m)
    return 1 if (survived or missing) else 0


if __name__ == '__main__':
    sys.exit(main())
