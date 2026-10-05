#!/usr/bin/env python3
"""Reproducible mutation evidence for the measuring-build PR: neuters ONE guard at a time and requires the DB-free suites of the PR
(test_horizon_derivation, test_mb_horizon_shape_guard, test_mb_interim_sink, test_c46_v5_test_slice, test_a53_gochara_v5_writer, the writer conformance test)
to fail for each. Files are restored in a `finally` block. Exit status is non-zero if any mutation survives or a target string is missing.

    python3 scripts/gochara/mutation_check_measuring_build.py [--list] [--only <text>]

Run from the platform/ directory; about 5 seconds per mutation (no database, no ephemeris)."""
import subprocess
import sys

K = "python-sidecar/services/gochara_kernel/"
W = "python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py"
TESTS = ["tests/l3/gochara/test_horizon_derivation.py", "tests/l3/gochara/test_mb_horizon_shape_guard.py", "tests/l3/gochara/test_mb_interim_sink.py",
         "tests/l3/gochara/test_c46_v5_test_slice.py", "tests/l3/gochara/test_a53_gochara_v5_writer.py", "tests/l3/gochara/test_a53_writerbase_conformance.py"]

MUTATIONS = [
    # the horizon START edge
    ("a start before the birth date is no longer refused", K + "horizon.py", "    if start < _utc_midnight(birth_date):", "    if False:"),
    ("a start in the future is no longer refused", K + "horizon.py", "    if start > _utc_midnight(build_date):", "    if False:"),
    ("the substrate-domain start edge is no longer checked in the derivation", K + "horizon.py",
     "    require_inside_substrate_domain((start, end))            # FB-3", "    pass                                                    # FB-3"),
    ("the domain check no longer refuses a start before the domain", K + "horizon.py", "    if start < SUBSTRATE_DOMAIN_START or end > SUBSTRATE_DOMAIN_END:", "    if end > SUBSTRATE_DOMAIN_END:"),
    ("a 29 February birth is guessed instead of refused", K + "horizon.py", "        return d.replace(year=d.year + years)\n    except ValueError:", "        return d.replace(year=d.year + years)\n    except ValueError:\n        return d.replace(year=d.year + years, day=28)\n    except KeyError:"),
    ("a not-fully-dated event can fix the start (the confidence flag is dropped)", K + "horizon.py", "    if m is None or event.date_confidence != \"exact\":\n        return False", "    if m is None:\n        return False"),
    ("the birth entry may fix the start", K + "horizon.py", "after_birth = [e for e in rows if e.event_date > birth_date]", "after_birth = [e for e in rows if e.event_date >= birth_date]"),
    ("the raw-row counts are not reported", K + "horizon.py", "excluded_not_fully_dated=len(after_birth) - len(dated)", "excluded_not_fully_dated=0"),
    # the writer's derivation and slice shapes
    ("an absent horizon falls back to the constant again", W, "        derived = _derive_horizon(ctx).bounds        # FB-2: absent = DERIVED, never a constant", "        derived = tuple(DEFAULT_HORIZON)             # FB-2: absent = DERIVED, never a constant"),
    ("all_classes_full accepts a subset of classes", W, "        if set(classes) != set(SCORED_CLASSES):\n            refuse(f\"run 'all_classes_full' is all", "        if False:\n            refuse(f\"run 'all_classes_full' is all"),
    ("all_classes_full accepts any horizon inside the bound", W, "        if tuple(horizon) != tuple(outer):\n            refuse(\"run 'all_classes_full'", "        if False:\n            refuse(\"run 'all_classes_full'"),
    ("the run-time slice outer bound is the constant, not the derivation", W, "    outer = _derive_horizon(ctx).bounds if ctx.config.get(\"birth_params\") else None", "    outer = None"),
    ("the manifest substep does not refuse a horizon outside the substrate domain", W, "                gk_horizon.require_inside_substrate_domain((horizon[0], horizon[1]))        # FB-3 for every source", "                pass                                                                         # FB-3 for every source"),
    # the basis pin
    ("the manifest vector is built without the basis", W, "                test_slice=_slice_component(slice_) if slice_ is not None else None,\n                horizon_basis=_horizon_basis(ctx, slice_))", "                test_slice=_slice_component(slice_) if slice_ is not None else None)"),
    ("the live check does not pass the re-derived basis", W, "        test_slice=_slice_component(slice_) if slice_ is not None else None,\n        horizon_basis=_horizon_basis(ctx, slice_))", "        test_slice=_slice_component(slice_) if slice_ is not None else None)"),
    ("the vector drops the basis when assembling", K + "input_vector.py", '      | ({"horizon_basis": inp["horizon_basis"]} if inp.get("horizon_basis") is not None else {})', "      | {}"),
    # the state guard
    ("the state guard no longer refuses a non-building row", W, '    if state != "building":\n        raise AssetNotBuilding(', '    if False:\n        raise AssetNotBuilding('),
    ("the state guard refuses an absent row", W, "    if row is None:\n        return\n    state = row[\"state\"]", "    if row is None:\n        raise AssetNotBuilding('absent')\n    state = row[\"state\"]"),
    ("the state guard runs in a dry run", W, "    if ctx.dry_run or ctx.db_conn is None:\n        return\n\n    def read():", "    if ctx.db_conn is None:\n        return\n\n    def read():"),
    ("the substep no longer calls the state guard", W, "        _require_building(ctx, chart_id)    # the state guard", "        pass    # the state guard"),
    # the interim sink
    ("an unresolved stretch is never recorded", K + "contact_certify.py", '                if reason in UNRESOLVED_REASONS:\n                    if stretch_sink is not None:', '                if reason in UNRESOLVED_REASONS:\n                    if False:'),
    ("the report policy still raises on an unresolved stretch", K + "contact_certify.py", "                    if unresolved_policy == UNRESOLVED_REPORT:\n                        continue", "                    if False:\n                        continue"),
    ("the report policy forgives a proven omission", K + "contact_certify.py", "                elif stretch_sink is not None:\n                    stretch_sink.append({**rec, \"class\": \"omission\"", "                elif unresolved_policy == UNRESOLVED_REPORT:\n                    continue\n                elif stretch_sink is not None:\n                    stretch_sink.append({**rec, \"class\": \"omission\""),
    ("the sink record never counts seams", K + "interim_sink.py", "        if stations:\n            seam_n += 1", "        if False:\n            seam_n += 1"),
    ("the sink record never finds wraps", K + "interim_sink.py", "    return min(lv, 360.0 - lv) <= orb_deg + 1e-9", "    return False"),
    ("the verify substep does not log the record when the certification raises", W, "        finally:\n            sink_record = None\n            if stretch_sink is not None:", "        except BaseException:\n            raise\n        else:\n            sink_record = None\n            if stretch_sink is not None:"),
    ("the measuring build raises on unresolved stretches", W, 'slice_.run == "all_classes_full"\n                  else gk_contact_certify.UNRESOLVED_RAISE)', 'slice_.run == "never"\n                  else gk_contact_certify.UNRESOLVED_RAISE)'),
]


def run_tests() -> bool:
    p = subprocess.run([sys.executable, "-m", "pytest", *TESTS, "-q", "-x", "-p", "no:cacheprovider"], cwd="python-sidecar", capture_output=True, text=True)
    return p.returncode == 0


def main() -> int:
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    if "--list" in sys.argv:
        for name, *_ in MUTATIONS:
            print(name)
        return 0
    if not run_tests():
        print("BASELINE FAILS: the suite is not green before any mutation")
        return 2
    survived = missing = 0
    for name, path, old, new in MUTATIONS:
        if only and only not in name:
            continue
        src = open(path, encoding="utf-8").read()
        if src.count(old) != 1:
            print(f"MISSING  {name}: target string found {src.count(old)} times in {path}")
            missing += 1
            continue
        try:
            open(path, "w", encoding="utf-8").write(src.replace(old, new))
            caught = not run_tests()
        finally:
            open(path, "w", encoding="utf-8").write(src)
        print(("CAUGHT   " if caught else "SURVIVED ") + name)
        survived += 0 if caught else 1
    print(f"{survived} survived, {missing} missing")
    return 1 if (survived or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
