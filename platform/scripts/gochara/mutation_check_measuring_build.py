#!/usr/bin/env python3
"""Reproducible mutation evidence for the measuring-build PR: neuters ONE guard at a time and requires the DB-free suites of the PR
(test_horizon_derivation, test_mb_horizon_shape_guard, test_mb_stretch_sink, test_c46_v5_test_slice, test_a53_gochara_v5_writer, the writer conformance test, the dispatch and
teardown unit tests) to FAIL BY ASSERTION for each (a mutant that only crashes the suite is BROKEN and does not count). Files are restored in a `finally` block. Exit status is
non-zero if any mutation survives, is broken, or a target string is missing.

    python3 scripts/gochara/mutation_check_measuring_build.py [--list] [--only <text>]

Run from the platform/ directory; about 5 seconds per mutation (no database, no ephemeris)."""
import subprocess
import sys

K = "python-sidecar/services/gochara_kernel/"
W = "python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py"
TESTS = ["tests/l3/gochara/test_horizon_derivation.py", "tests/l3/gochara/test_mb_horizon_shape_guard.py", "tests/l3/gochara/test_mb_stretch_sink.py",
         "tests/l3/gochara/test_c46_v5_test_slice.py", "tests/l3/gochara/test_a53_gochara_v5_writer.py", "tests/l3/gochara/test_a53_writerbase_conformance.py",
         "../scripts/__tests__/test_dispatch_v5_small_test.py", "../scripts/__tests__/test_teardown_v5_small_test.py"]
#: a mutation is only KILLED by a test that fails on what it ASSERTS (an `assert`, a `DID NOT RAISE`, a refusal of another name, a wrong value); a mutant that merely
#: crashes the suite (a failure line naming one of these exception types, or any collection error) is BROKEN: reported, and counted as not caught, so its text must be fixed.
CRASH_TYPES = ("AttributeError", "NameError", "UnboundLocalError", "TypeError", "SyntaxError", "IndentationError", "ImportError", "ModuleNotFoundError", "IndexError", "KeyError")

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
    ("the id rule accepts every row", H, "    m = _FULLY_DATED_ID.match(e.provenance_lel_id or \"\")\n    if m is None or e.event_date is None:\n        return False", "    return True\n    m = _FULLY_DATED_ID.match(e.provenance_lel_id or \"\")\n    if m is None or e.event_date is None:\n        return False"),
    ("the event_id is used as a fallback for a missing lel_id", H, "    m = _FULLY_DATED_ID.match(e.provenance_lel_id or \"\")\n    if m is None or e.event_date is None:\n        return False", "    m = _FULLY_DATED_ID.match(e.provenance_lel_id or e.event_id)\n    if m is None or e.event_date is None:\n        return False"),
    ("rows without a lel_id are not reported in the basis", H, "        no_id = tuple({\"event_id\": e.event_id, \"event_date\": _iso(e.event_date)} for e in others if not has_lel_id(e))", "        no_id = ()"),
    ("a blank lel_id counts as an id", H, "    return bool((e.provenance_lel_id or \"\").strip())", "    return e.provenance_lel_id is not None"),
    ("a log with no dated event falls back to the build date", H, "        if first_event is None:\n            raise HorizonUnderivableLogHasNoDatedEvent(", "        if False:\n            raise HorizonUnderivableLogHasNoDatedEvent("),
    ("the birth row is not required to carry the birth domain", H, "    return e.event_date == birth_date and e.domain == BIRTH_DOMAIN", "    return e.event_date == birth_date"),
    ("the provenance subcategory identifies the birth row again", H, "    return e.event_date == birth_date and e.domain == BIRTH_DOMAIN", "    return e.event_date == birth_date and (e.domain == BIRTH_DOMAIN or e.provenance_subcategory == \"birth\")"),
    ("a non-empty log without exactly one birth row is accepted", H, "        if len(candidates) != 1:\n            raise LelBirthRowUnidentifiable(", "        if False:\n            raise LelBirthRowUnidentifiable("),
    ("a shape-sensitive start is no longer refused", H, "        if len(set(shape_readings.values())) != 1:", "        if False:"),
    ("the ruling guard is gone", H, "    if ruled is not None and (start, end) != tuple(ruled):", "    if False:"),
    ("an unknown confidence word is accepted", H, "    bad = [e.event_id for e in rows if e.date_confidence not in CONFIDENCES]\n    if bad:", "    bad = []\n    if bad:"),
    ("the consumed rows are not pinned in the basis", H, "\"rows_total\": len(self.consumed_rows), \"consumed_rows\": [dict(r) for r in self.consumed_rows],", "\"rows_total\": len(self.consumed_rows), \"consumed_rows\": [],"),
    # the writer: scope of the derivation, the shapes, the basis pin and the live check
    ("an ordinary build derives its horizon from the log again", W, "    if slice_ is None:\n        return ctx.config.get(\"horizon\", DEFAULT_HORIZON)", "    if slice_ is None:\n        return _derive_horizon(ctx).bounds"),
    ("an ordinary build is handed a basis", W, "    if slice_ is None or slice_.run != MEASURING_RUN:\n        return None", "    if slice_ is None and False:\n        return None"),
    ("the two older shapes are validated against the measuring horizon", W, "    if run == MEASURING_RUN:\n        return MEASURING_HORIZON if outer is None else outer\n    return DEFAULT_HORIZON", "    if True:\n        return MEASURING_HORIZON if outer is None else outer\n    return DEFAULT_HORIZON"),
    ("the older shapes read the log through the run-time outer bound", W, "    if isinstance(marker, dict) and marker.get(\"run\") == MEASURING_RUN and ctx.config.get(\"birth_params\")", "    if isinstance(marker, dict) and ctx.config.get(\"birth_params\")"),
    ("the derivation reads every chart's rows", W, "FROM public.life_events WHERE chart_id = %s ORDER BY event_date, event_id\",\n            (chart_id,)).fetchall())]", "FROM public.life_events WHERE %s = %s ORDER BY event_date, event_id\",\n            (chart_id, chart_id)).fetchall())]"),
    ("the ruling guard is not passed for the pinned chart", W, "ruled=gk_horizon.RULED_HORIZONS.get(chart_id) if ruling else None)", "ruled=None)"),
    ("the plan-time ruling guard is gone", W, "    if pinned is None:\n        return _derive_horizon(ctx).bounds", "    if pinned is None:\n        return _derive_horizon(ctx, ruling=False).bounds"),
    ("the ruling guard runs BEFORE the pinned basis is compared", W, "    pinned = _pinned_horizon_basis(ctx)\n    if pinned is None:\n        return _derive_horizon(ctx).bounds", "    pinned = None\n    if pinned is None:\n        return _derive_horizon(ctx).bounds"),
    ("a changed horizon is not refused by the pinned comparison", W, "    _raise_if_horizon_changed(live.basis_record(), pinned)\n    return live.bounds", "    return live.bounds"),
    ("all_classes_full accepts a subset of classes", W, "        if set(classes) != set(SCORED_CLASSES):\n            refuse(f\"run 'all_classes_full' is all", "        if False:\n            refuse(f\"run 'all_classes_full' is all"),
    ("all_classes_full accepts any horizon inside the bound", W, "        if tuple(horizon) != tuple(outer):\n            refuse(\"run 'all_classes_full'", "        if False:\n            refuse(\"run 'all_classes_full'"),
    ("the run-time slice outer bound is the constant, not the derivation", W, "        outer = _derived_outer_bound(ctx)", "        outer = None"),
    ("the manifest substep does not refuse a measuring horizon outside the substrate domain", W, "                gk_horizon.require_inside_substrate_domain((horizon[0], horizon[1]))        # FB-3 for the measuring", "                pass                                                                         # FB-3 for the measuring"),
    ("the manifest vector is built without the basis", W, "                test_slice=_slice_component(slice_) if slice_ is not None else None,\n                horizon_basis=_horizon_basis(ctx, slice_))", "                test_slice=_slice_component(slice_) if slice_ is not None else None)"),
    ("the live check does not compare the basis", W, "        horizon_basis=_live_basis_for_check(ctx, slice_, stored))", "        horizon_basis=stored.get(\"horizon_basis\"))"),
    ("a log edit that does not change the horizon still drifts the vector", W, "    if live.get(\"horizon\") != pinned.get(\"horizon\") or live.get(\"basis\") != pinned.get(\"basis\"):\n        raise HorizonBasisHorizonChanged(", "    if True:\n        raise HorizonBasisHorizonChanged("),
    ("a log edit that changes the horizon is forgiven", W, "    if live.get(\"horizon\") != pinned.get(\"horizon\") or live.get(\"basis\") != pinned.get(\"basis\"):\n        raise HorizonBasisHorizonChanged(", "    if False:\n        raise HorizonBasisHorizonChanged("),
    ("the vector drops the basis when assembling", K + "input_vector.py", '      | ({"horizon_basis": inp["horizon_basis"]} if inp.get("horizon_basis") is not None else {})', "      | {}"),
    # the state guard (MB-4)
    ("the state guard no longer refuses a non-building row", W, '    if state != "building":\n        raise AssetNotBuilding(', '    if False:\n        raise AssetNotBuilding('),
    ("the state guard's message loses its token", W, 'f"asset_not_building: {ASSET_ID}: asset_throughput.state', 'f"{ASSET_ID}: asset_throughput.state'),
    ("the state guard refuses an absent row", W, "    if row is None:\n        return\n    state = row[\"state\"]", "    if row is None:\n        raise AssetNotBuilding('absent')\n    state = row[\"state\"]"),
    ("the state guard runs in a dry run", W, "    if ctx.dry_run or ctx.db_conn is None:\n        return\n\n    def read():", "    if ctx.db_conn is None:\n        return\n\n    def read():"),
    ("the substep no longer calls the state guard", W, "        _require_building(ctx, chart_id)    # the state guard", "        pass    # the state guard"),
    # the collection policy (MB-2.1)
    ("the default policy takes the collect-everything path", C, "    if sink_policy == POLICY_SINK_ALL:\n        if stretch_sink is None:", "    if True:\n        if stretch_sink is None:"),
    ("an invented ledger contact is not recorded", C, "    for h in union:\n        if any(same(w, h) for w in want):\n            continue", "    for h in union:\n        if True:\n            continue"),
    ("a touched but disagreeing stretch is recorded as a plain contact", C, "            if agrees:\n                stretch_sink.append({**rec, \"kind\": \"contact\", \"reason\": None})", "            if True:\n                stretch_sink.append({**rec, \"kind\": \"contact\", \"reason\": None})"),
    ("the obligation-level pairing anomaly is not recorded", C, "    if not unmatched_w and not unmatched_h and not (", "    if False and not unmatched_w and not unmatched_h and not ("),
    ("an anomaly stretch is not recorded under sink_all", C, "        stretch_sink.append({**rec, \"kind\": kind, \"reason\": why, \"detail\": detail, **extra})\n        if g is not None and graze_sink is not None:", "        if kind != \"anomaly\":\n            stretch_sink.append({**rec, \"kind\": kind, \"reason\": why, \"detail\": detail, **extra})\n        if g is not None and graze_sink is not None:"),
    ("an extension that cannot be settled loses its detail under sink_all", C, "\n        detail = _full_stretch.last_detail if reason == REASON_EXTENSION_NOT_SETTLED else None", "\n        detail = None"),
    # the record, its id and its vocabulary (MB-2.2, 2.3)
    ("the station seam is never recorded", S, "        if stations:\n            out.append(_record(\"station_seam\"", "        if False:\n            out.append(_record(\"station_seam\""),
    ("a station seam needs no overlapping ledger contact", S, "if episodes >= 1 else []", "if True else []"),
    ("a seam does not carry station_at", S, "station_at=sorted(stations)[0],", "station_at=None,"),
    ("a multi-episode stretch needs three episodes", S, "        if episodes >= 2:", "        if episodes >= 3:"),
    ("the wrap cut is never found", S, "    return min(lv, 360.0 - lv) <= orb_deg + 1e-9", "    return False"),
    ("the record id ignores the stretch ordinal", S, "_instant(horizon[1]), str(int(stretch_ordinal))))", "_instant(horizon[1])))"),
    ("the record id ignores the horizon", S, "_instant(horizon[0]), _instant(horizon[1]), str(int(stretch_ordinal))))", "str(int(stretch_ordinal))))"),
    ("the orb is formatted without %.3f", S, "\"0.000\" if orb_deg is None else \"%.3f\" % float(orb_deg)", "\"0.000\" if orb_deg is None else str(float(orb_deg))"),
    ("a residence obligation has no 0.000 orb", S, "orb = \"0.000\" if orb_deg is None", "orb = \"None\" if orb_deg is None"),
    ("a word outside the closed table is accepted", S, "    if rec[\"reason\"] not in KIND_REASONS.get(rec[\"kind\"], ()):", "    if False:"),
    ("the summary digest is not of the sorted ids", S, r'"record_ids_digest": hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()}', r'"record_ids_digest": hashlib.sha256(b"").hexdigest()}'),
    ("the measuring build raises on what it should sink", W, 'slice_.run == "all_classes_full" else gk_contact_certify.POLICY_RAISE)', 'slice_.run == "never" else gk_contact_certify.POLICY_RAISE)'),
    ("the records are not logged when the certification raises", W, "        finally:\n            if stretch_sink is not None:\n                sink_summary", "        except BaseException:\n            raise\n        else:\n            if stretch_sink is not None:\n                sink_summary"),
]


def run_tests() -> str:
    """"green" | "killed" (at least one assertion-type failure) | "broken" (it failed, but only by crashing)."""
    p = subprocess.run([sys.executable, "-m", "pytest", *TESTS, "-q", "-p", "no:cacheprovider", "-rf", "--tb=line"], cwd="python-sidecar", capture_output=True, text=True)
    if p.returncode == 0:
        return "green"
    if p.returncode != 1:
        return "broken"                                    # interrupted, internal error, usage error, or nothing collected
    failures = [ln for ln in p.stdout.splitlines() if ln.startswith(("FAILED ", "ERROR "))]
    if any(ln.startswith("ERROR ") for ln in failures):
        return "broken"                                    # a collection or setup error
    return "killed" if any(ln.startswith("FAILED ") and not any(f" {t}" in ln.split(" - ", 1)[-1][:60] for t in CRASH_TYPES) for ln in failures) else "broken"


def main() -> int:
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    if "--list" in sys.argv:
        for name, *_ in MUTATIONS:
            print(name)
        return 0
    if run_tests() != "green":
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
            outcome = run_tests()
        finally:
            open(path, "w", encoding="utf-8").write(src)
        print({"killed": "CAUGHT   ", "green": "SURVIVED ", "broken": "BROKEN   (crashed the suite without an assertion: not a kill) "}[outcome] + name)
        survived += 0 if outcome == "killed" else 1
    print(f"{survived} survived, {missing} missing")
    return 1 if (survived or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
