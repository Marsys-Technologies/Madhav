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
TESTS = ["tests/l3/gochara/test_horizon_derivation.py", "tests/l3/gochara/test_mb_horizon_shape_guard.py", "tests/l3/gochara/test_mb_stretch_sink.py",
         "tests/l3/gochara/test_c46_v5_test_slice.py", "tests/l3/gochara/test_a53_gochara_v5_writer.py", "tests/l3/gochara/test_a53_writerbase_conformance.py"]

H, S, C = K + "horizon.py", K + "stretch_sink.py", K + "contact_certify.py"
MUTATIONS = [
    # the horizon detector (MB-1)
    ("a start before the birth date is no longer refused", H, "    if start < _utc_midnight(birth_date):", "    if False:"),
    ("a start in the future is no longer refused", H, "    if start > _utc_midnight(build_date):", "    if False:"),
    ("a start before the substrate domain is no longer refused in the derivation", H, "    if start < SUBSTRATE_DOMAIN_START:\n        raise HorizonStartBeforeSubstrateDomain(f\"the start", "    if False:\n        raise HorizonStartBeforeSubstrateDomain(f\"the start"),
    ("an end after the substrate domain is no longer refused in the derivation", H, "    if end > SUBSTRATE_DOMAIN_END:\n        raise HorizonOutsideSubstrateDomain(f\"the end", "    if False:\n        raise HorizonOutsideSubstrateDomain(f\"the end"),
    ("an empty horizon is no longer refused", H, "    if not start < end:\n        raise HorizonEmpty(", "    if False:\n        raise HorizonEmpty("),
    ("a 29 February birth is guessed instead of refused", H, "        return d.replace(year=d.year + years)\n    except ValueError:", "        return d.replace(year=d.year + years)\n    except ValueError:\n        return d.replace(year=d.year + years, day=28)\n    except KeyError:"),
    ("the flag rule accepts every row", H, "    return e.date_confidence == \"exact\"", "    return True"),
    ("the id rule accepts every row", H, "    m = _FULLY_DATED_ID.match(e.event_id or \"\")\n    if m is None or e.event_date is None:\n        return False", "    return True\n    m = _FULLY_DATED_ID.match(e.event_id or \"\")\n    if m is None or e.event_date is None:\n        return False"),
    ("the two dating rules may disagree on the first event", H, "        if dating_rules[\"flag_exact\"] != dating_rules[\"id_digits\"]:", "        if False:"),
    ("the birth row is not required to carry the birth word", H, "candidates = [e for e in rows if e.event_date == birth_date and e.birth_word == BIRTH_WORD]", "candidates = [e for e in rows if e.event_date == birth_date]"),
    ("an unpinned birth-word column is no longer refused", H, "        if birth_word_column is None:\n            raise LelBirthRowUnidentifiable(", "        if False:\n            raise LelBirthRowUnidentifiable("),
    ("a shape-sensitive start is no longer refused", H, "        if len(set(readings.values())) != 1:", "        if False:"),
    ("the ruling guard is gone", H, "    if ruled is not None and (start, end) != tuple(ruled):", "    if False:"),
    ("an unknown confidence word is accepted", H, "    bad = [e.event_id for e in rows if e.date_confidence not in CONFIDENCES]\n    if bad:", "    bad = []\n    if bad:"),
    ("the consumed rows are not pinned in the basis", H, "\"basis\": self.basis, \"chosen\": chosen, \"birth_row\": birth, \"consumed_rows\": [dict(r) for r in self.consumed_rows],", "\"basis\": self.basis, \"chosen\": chosen, \"birth_row\": birth, \"consumed_rows\": [],"),
    # the writer's derivation, shapes, basis pin and live check
    ("an absent horizon falls back to the constant again", W, "        derived = _derive_horizon(ctx).bounds        # FB-2: absent = DERIVED, never a constant", "        derived = tuple(DEFAULT_HORIZON)             # FB-2: absent = DERIVED, never a constant"),
    ("the derivation reads every chart's rows", W, "FROM public.life_events WHERE chart_id = %s ORDER BY event_date, event_id\", (chart_id,)", "FROM public.life_events WHERE %s = %s ORDER BY event_date, event_id\", (chart_id, chart_id)"),
    ("the ruling guard is not passed for the pinned chart", W, "birth_word_column=word_col, ruled=gk_horizon.RULED_HORIZONS.get(chart_id))", "birth_word_column=word_col, ruled=None)"),
    ("the plan-time ruling guard is gone", W, "            _derive_horizon(ctx)         # MB-1.2 item 7", "            pass                         # MB-1.2 item 7"),
    ("all_classes_full accepts a subset of classes", W, "        if set(classes) != set(SCORED_CLASSES):\n            refuse(f\"run 'all_classes_full' is all", "        if False:\n            refuse(f\"run 'all_classes_full' is all"),
    ("all_classes_full accepts any horizon inside the bound", W, "        if tuple(horizon) != tuple(outer):\n            refuse(\"run 'all_classes_full'", "        if False:\n            refuse(\"run 'all_classes_full'"),
    ("the run-time slice outer bound is the constant, not the derivation", W, "    outer = _derive_horizon(ctx).bounds if ctx.config.get(\"birth_params\") else None", "    outer = None"),
    ("the manifest substep does not refuse a horizon outside the substrate domain", W, "                gk_horizon.require_inside_substrate_domain((horizon[0], horizon[1]))        # FB-3 for every source", "                pass                                                                         # FB-3 for every source"),
    ("the manifest vector is built without the basis", W, "                test_slice=_slice_component(slice_) if slice_ is not None else None,\n                horizon_basis=_horizon_basis(ctx, slice_))", "                test_slice=_slice_component(slice_) if slice_ is not None else None)"),
    ("the live check does not compare the basis", W, "        horizon_basis=_live_basis_for_check(ctx, slice_, stored))", "        horizon_basis=stored.get(\"horizon_basis\"))"),
    ("a log edit that does not change the horizon still drifts the vector", W, "    if live.get(\"horizon\") != pinned.get(\"horizon\") or live.get(\"basis\") != pinned.get(\"basis\"):\n        return live", "    if True:\n        return live"),
    ("a log edit that changes the horizon is forgiven", W, "    if live.get(\"horizon\") != pinned.get(\"horizon\") or live.get(\"basis\") != pinned.get(\"basis\"):\n        return live", "    if False:\n        return live"),
    ("the vector drops the basis when assembling", K + "input_vector.py", '      | ({"horizon_basis": inp["horizon_basis"]} if inp.get("horizon_basis") is not None else {})', "      | {}"),
    # the state guard (MB-4)
    ("the state guard no longer refuses a non-building row", W, '    if state != "building":\n        raise AssetNotBuilding(', '    if False:\n        raise AssetNotBuilding('),
    ("the state guard's message loses its token", W, 'f"asset_not_building: {ASSET_ID}: asset_throughput.state', 'f"{ASSET_ID}: asset_throughput.state'),
    ("the state guard refuses an absent row", W, "    if row is None:\n        return\n    state = row[\"state\"]", "    if row is None:\n        raise AssetNotBuilding('absent')\n    state = row[\"state\"]"),
    ("the state guard runs in a dry run", W, "    if ctx.dry_run or ctx.db_conn is None:\n        return\n\n    def read():", "    if ctx.db_conn is None:\n        return\n\n    def read():"),
    ("the substep no longer calls the state guard", W, "        _require_building(ctx, chart_id)    # the state guard", "        pass    # the state guard"),
    # the sink and its policy (MB-2)
    ("an omission is not sunk in the measuring build", C, 'SUNK_KINDS_UNDER_SINK_ALL = ("near_miss", "unresolved", "omission")', 'SUNK_KINDS_UNDER_SINK_ALL = ("near_miss", "unresolved")'),
    ("an unresolved stretch is not sunk in the measuring build", C, 'SUNK_KINDS_UNDER_SINK_ALL = ("near_miss", "unresolved", "omission")', 'SUNK_KINDS_UNDER_SINK_ALL = ("near_miss", "omission")'),
    ("an anomaly is sunk in the measuring build", C, 'SUNK_KINDS_UNDER_SINK_ALL = ("near_miss", "unresolved", "omission")', 'SUNK_KINDS_UNDER_SINK_ALL = ("near_miss", "unresolved", "omission", "anomaly")'),
    ("the default policy sinks everything", C, "            if sink_policy == POLICY_SINK_ALL and kind in SUNK_KINDS_UNDER_SINK_ALL:", "            if kind in SUNK_KINDS_UNDER_SINK_ALL:"),
    ("a ledger-touched mismatch is forgiven under sink_all", C, "            if episodes:\n                if stretch_sink is not None:", "            if episodes and sink_policy == POLICY_SINK_ALL:\n                continue\n            if episodes:\n                if stretch_sink is not None:"),
    ("a clipped extension never records its detail", C, "                detail = {\"extension\": _full_stretch.last_detail} if reason == REASON_EXTENSION_NOT_SETTLED else None", "                detail = None"),
    ("the station seam is never recorded", S, "        if stations:\n            out.append(_record(\"station_seam\"", "        if False:\n            out.append(_record(\"station_seam\""),
    ("a multi-episode stretch needs three episodes", S, "        if (st.get(\"episode_count\") or 0) >= 2:", "        if (st.get(\"episode_count\") or 0) >= 3:"),
    ("the wrap cut is never found", S, "    return min(lv, 360.0 - lv) <= orb_deg + 1e-9", "    return False"),
    ("the record id ignores the stretch ordinal", S, "{orb_deg}|{horizon[0].isoformat()}|{horizon[1].isoformat()}|{stretch_ordinal}\"", "{orb_deg}|{horizon[0].isoformat()}|{horizon[1].isoformat()}\""),
    ("the record id ignores the horizon", S, "|{orb_deg}|{horizon[0].isoformat()}|{horizon[1].isoformat()}|{stretch_ordinal}\"", "|{orb_deg}|{stretch_ordinal}\""),
    ("the summary digest is not of the sorted ids", S, r'"record_ids_digest": hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()}', r'"record_ids_digest": hashlib.sha256(b"").hexdigest()}'),
    ("the measuring build raises on what it should sink", W, 'slice_.run == "all_classes_full" else gk_contact_certify.POLICY_RAISE)', 'slice_.run == "never" else gk_contact_certify.POLICY_RAISE)'),
    ("the records are not logged when the certification raises", W, "        finally:\n            if stretch_sink is not None:\n                sink_summary", "        except BaseException:\n            raise\n        else:\n            if stretch_sink is not None:\n                sink_summary"),
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
