"""J-4d by slice: qualify the final-rules candidate on a three-class slice (SR-BOLD-03, owner-confirmed OWNER-BOLD-CONFIRM-20261018).

SR-BOLD-03 replaces the full-horizon final-rules lane build with a slice: the heaviest class by the measuring build's REAL per-class
timings plus two others, built on the lane database, with J-4c's equality and non-interference proofs run against the measuring golden
for those classes only. Qualified = slice built, both proofs pass, P06b complete. ANY defect = FULL_BUILD_REQUIRED (the full lane
build runs instead). J-5q still fully qualifies the production candidate before sealing; this module qualifies nothing else.

What each part measures (CLAUDE.md N.8: every verdict part has a detector that can read false):

  * class choice      `class_costs` / `choose_slice`: per-class seconds from J-3c's `by_class_substep` timings, summed over a class's
                      substeps; the heaviest class is always in the slice; exactly three distinct scored classes.
  * lane build        `build_slice`: the writer's OWN plan (`GocharaV5Writer.plan_substeps`) restricted to the slice classes, each substep
                      driven in its own transaction with `gochara_v5_final_rules=True`; any raised substep or any `UNVERIFIED` outcome is a
                      defect. Refuses any database that is not the local lane (127.0.0.1:55433).
  * equality proof    `equality_proof`: for every (class, path) cell whose rule selection is the SAME under both profiles, the slice's records,
                      windows and referenced contacts equal the golden's byte for byte (canonical JSON). Vacuous (nothing compared) = fail.
  * non-interference  `noninterference_proof`: for every cell the final rules DO change, no record of the measuring rule version leaks in
                      and a cell the final rules suppress holds no row; and the measuring (default) rule profile is still the default
                      after the final-rules build (the profile did not leak out of its context).
  * P06b              `p06b_complete`: the plan model's own P06b detector (path + pattern) applied to the receipt file.

(I) INTERPRETATION: "non-interference: the measuring rules' outputs unchanged" is measured as the two cell-level checks above, i.e. what the
golden's stored columns can establish. `near_miss_verifier.noninterference_problems` needs fourteen output sets (five live endpoints
among them) that neither the golden nor a slice carries; feeding it placeholders would be a green nothing measured, so the verdict lists
them under `cannot_establish` and leaves them to P06b / J-5q. Alternative: call it with sentinel values (rejected, N.8).

(I) INTERPRETATION: the two non-heaviest classes default to the next costliest classes, except that the slice must hold at least one class
whose rule selection is identical under both profiles (otherwise the equality proof has little to compare); the costliest such class
replaces the third pick when the three costliest have none. Explicit `--classes` always wins (it must still contain the heaviest class
when a timings file is given).

Lane database only. Never production; never a commit; the caller owns the connection's database lifecycle.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from services.gochara_kernel import measuring_capture as mc
from services.gochara_kernel import measuring_report as mr
from services.gochara_kernel import rule_registry as rr

SCHEMA = "ky.j4d_slice_verdict/1"
QUALIFIED = "QUALIFIED"
FULL_BUILD_REQUIRED = "FULL_BUILD_REQUIRED"
SLICE_SIZE = 3
LANE_PORT = 55433
LANE_DB_NAME = re.compile(r"(?:ky_[a-z0-9_]+|a53t_[a-z0-9_]+)")
GENERATION = "5.0"
REPO = Path(__file__).resolve().parents[4]
PLAN_MODEL = REPO / "00_ARCHITECTURE" / "control" / "kalayantra" / "plan_model.json"
CANNOT_ESTABLISH = (
    "near-miss layer on/off over the 14 NONINTERFERENCE_KEYS and the five live endpoints (P06b / J-5q)",
    "seal, publication and the full-horizon, all-class final candidate (J-5q)",
    "independent acceptance of this verdict (a reviewer job, not this harness)",
)


class SliceRefused(ValueError):
    """An input the harness will not guess about; never a verdict."""


# ── class choice ─────────────────────────────────────────────────────────────────────────────────────────────────

def _timings_of(doc: Any) -> dict:
    """The `timings` section of J-3c's observations file, or of its draft report (numbers['1'].data)."""
    if isinstance(doc, dict) and isinstance(doc.get("timings"), dict):
        return doc["timings"]
    if isinstance(doc, dict) and isinstance(doc.get("numbers"), dict):
        data = doc["numbers"].get("1", {}).get("data")
        if isinstance(data, dict):
            return data
    raise SliceRefused("timings_section_missing: expected `timings` or `numbers.1.data`")


def class_costs(doc: Any) -> dict[str, float]:
    """Seconds per scored class: the sum of every `by_class_substep` entry whose key names that class
    (a ':'-separated token, e.g. 'marriage:record' or 'record:marriage:P1'). Entries naming no scored class are not guessed at."""
    by_substep = _timings_of(doc).get("by_class_substep")
    if not isinstance(by_substep, dict) or not by_substep:
        raise SliceRefused("timings_by_class_substep_missing")
    costs: Counter = Counter()
    for key, seconds in by_substep.items():
        if type(seconds) not in (int, float) or seconds != seconds or seconds < 0 or seconds == float("inf"):
            raise SliceRefused(f"timing_invalid: {key!r}")
        named = [t for t in str(key).split(":") if t in mr.SCORED_CLASSES]
        if len(named) == 1:
            costs[named[0]] += seconds
    if not costs:
        raise SliceRefused("timings_name_no_scored_class")
    return dict(costs)


def _heaviest_first(costs: dict[str, float]) -> list[str]:
    return sorted(costs, key=lambda c: (-costs[c], c))        # total order: ties break by name


def cell_expectation(event_class: str, path_id: str) -> dict:
    """What the FINAL rules do to one (class, path) cell relative to the measuring (default) rules, read from the registry itself.

    kind 'same'      -> selection and emission identical under both profiles: the cell must equal the golden;
    kind 'final'     -> a different rule version is selected: the cell's records carry exactly that version;
    kind 'suppressed'-> the final rules emit no row (ND-H item 5, parental P2): the cell holds no record.
    """
    with rr.rule_profile(final_rules=False):
        base_version, base_none = rr.selected_versions_for(event_class)[path_id], path_id == "P2" and rr.p2_emits_no_row(event_class)
    with rr.rule_profile(final_rules=True):
        final_version, final_none = rr.selected_versions_for(event_class)[path_id], path_id == "P2" and rr.p2_emits_no_row(event_class)
    if final_none and not base_none:
        return {"kind": "suppressed", "measuring_version": base_version, "final_version": None}
    if final_version != base_version:
        return {"kind": "final", "measuring_version": base_version, "final_version": final_version}
    return {"kind": "same", "measuring_version": base_version, "final_version": final_version}


def is_unchanged_class(event_class: str) -> bool:
    return all(cell_expectation(event_class, p)["kind"] == "same" for p in ("P1", "P2", "P3", "P4"))


def choose_slice(*, timings: Any = None, classes: list[str] | tuple[str, ...] | None = None) -> dict:
    """The slice: explicit class ids, or derived from J-3c's real timings. Returns {'classes', 'heaviest', 'costs', 'source'}."""
    costs = class_costs(timings) if timings is not None else None
    if classes is not None:
        chosen = list(classes)
        if len(chosen) != SLICE_SIZE or len(set(chosen)) != SLICE_SIZE:
            raise SliceRefused(f"slice_not_three_distinct_classes: {chosen!r}")
        unknown = [c for c in chosen if c not in mr.SCORED_CLASSES]
        if unknown:
            raise SliceRefused(f"slice_class_not_scored: {unknown!r}")
        heaviest = None
        if costs is not None:
            heaviest = _heaviest_first(costs)[0]
            if heaviest not in chosen:
                raise SliceRefused(f"slice_misses_heaviest_class: {heaviest!r} not in {chosen!r}")
        return {"classes": sorted(chosen), "heaviest": heaviest, "costs": costs, "source": "explicit"}
    if costs is None:
        raise SliceRefused("no_class_ids_and_no_timings")
    order = _heaviest_first(costs)
    chosen = order[:SLICE_SIZE]
    if len(chosen) < SLICE_SIZE:
        raise SliceRefused(f"timings_name_fewer_than_three_classes: {order!r}")
    if not any(is_unchanged_class(c) for c in chosen):
        spare = next((c for c in order[SLICE_SIZE:] if is_unchanged_class(c)), None)
        if spare is None:
            spare = next((c for c in sorted(mr.SCORED_CLASSES) if c not in chosen and is_unchanged_class(c)), None)
        chosen = chosen[:SLICE_SIZE - 1] + [spare]
    return {"classes": sorted(chosen), "heaviest": order[0], "costs": costs, "source": "timings"}


# ── the lane database ────────────────────────────────────────────────────────────────────────────────────────────

def require_lane(conn: Any) -> None:
    """The local lane cluster only: loopback server, port 55433, a lane/disposable database name. A name alone is not enough
    (a local proxy can reach production), so the server's own address and port are read."""
    name, address, port = conn.execute("SELECT current_database(), inet_server_addr()::text, inet_server_port()").fetchone()
    if not LANE_DB_NAME.fullmatch(name or ""):
        raise SliceRefused("not_a_lane_database")
    if address is not None:
        ip = ipaddress.ip_interface(address).ip
        if not ip.is_loopback:
            raise SliceRefused("not_a_local_lane_server")
    if port != LANE_PORT:
        raise SliceRefused(f"not_the_lane_cluster_port: {port!r}")


def _aware(value: str) -> datetime:
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        raise SliceRefused(f"naive_horizon_bound: {value!r}")
    return moment.astimezone(timezone.utc)


def build_slice(conn: Any, *, chart_id: str, horizon: tuple, classes: list[str], ephe_path: str, birth_params: dict | None = None,
                build_id: str = "j4d-slice", head: tuple | None = None, kinds: tuple | None = None,
                paths: tuple | None = None, on_step: Callable[[str, Any], None] | None = None) -> dict:
    """Drive the writer's real plan, restricted to `classes`, under the FINAL rules, one transaction per substep.

    `conn` must be an autocommit lane connection. `head` / `kinds` / `paths` narrow the class-less substeps and the per-class substep kinds
    and paths (a harness on a stubbed L1 and a pre-built substrate cannot run them all); the lane run leaves all three None. Returns {'steps', 'defects'}; the first raised substep stops the build and is a defect.
    """
    from pipeline.orchestrator.writers import ContextSpec, ka_gochara_v5 as writer_mod

    require_lane(conn)
    config = {"chart_id": chart_id, "horizon": tuple(horizon), "ephe_path": ephe_path, "gochara_v5_final_rules": True}
    if birth_params:
        config["birth_params"] = birth_params
    ctx = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id=build_id, db_conn=conn, dry_run=False, config=config)
    writer = writer_mod.GocharaV5Writer()
    wanted = set(classes)
    plan = [s for s in writer.plan_substeps(ctx) if writer_mod._class_of_grain(s.key) in wanted | {None}]
    if head is not None:
        plan = [s for s in plan if writer_mod._class_of_grain(s.key) is not None or s.key in head]
    if kinds is not None:
        plan = [s for s in plan if writer_mod._class_of_grain(s.key) is None or s.key.split(":", 1)[0] in kinds]
    if paths is not None:
        plan = [s for s in plan if s.key.split(":")[-1] not in ("P1", "P2", "P3", "P4") or s.key.split(":")[-1] in paths]
    steps, defects = [], []
    for step in plan:
        try:
            with conn.transaction():
                result = writer.run_substep(ctx, step)
        except Exception as exc:                                           # noqa: BLE001 — every raised substep is a named defect
            defects.append({"step": step.key, "defect": "substep_raised", "detail": f"{type(exc).__name__}: {exc}"})
            break
        steps.append({"step": step.key, "rows": result.rows_inserted})
        if "UNVERIFIED" in (result.notes or ""):
            defects.append({"step": step.key, "defect": "unverified", "detail": result.notes})
        if on_step is not None:
            on_step(step.key, result)
    return {"steps": steps, "defects": defects}


def read_slice(conn: Any, *, chart_id: str, classes: list[str], generation: str = GENERATION) -> dict:
    """The slice's stored rows in the golden's own canonical form (measuring_capture), chart AND generation scoped, slice classes only."""
    require_lane(conn)
    pair, wanted = (chart_id, generation), list(classes)
    records = mc._rows(conn, "SELECT r.*, COALESCE((SELECT jsonb_agg(jsonb_build_array(p.predicate_id, p.predicate_rule_version) ORDER BY p.ordinal)"
                       " FROM public.ka_gochara_record_prerequisite p WHERE p.record_id = r.record_id"
                       " AND p.chart_id = r.chart_id AND p.generation = r.generation), '[]'::jsonb) AS prerequisites"
                       " FROM public.ka_gochara_relationship_record r WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = ANY(%s)",
                       (*pair, wanted))
    windows = mc._rows(conn, "SELECT event_class, path_id, rule_version, lower(interval) AS lo, upper(interval) AS hi"
                       " FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s)", (*pair, wanted))
    contact_ids = sorted({str(r["contact_id"]) for r in records if r["contact_id"] is not None})     # natal-relation rows carry no contact
    contacts = mc._rows(conn, "SELECT c.contact_id, c.body, c.relation_kind, o.canonical_target, c.t_in, c.t_out, c.t_exact, c.delta_lambda"
                        " FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o ON o.physical_object_id = c.physical_object_id"
                        " WHERE c.chart_id = %s AND c.generation = %s AND c.contact_id::text = ANY(%s)", (*pair, contact_ids))
    return {"records": [mc.golden_record(r) for r in records], "windows": [mc._plain(w) for w in windows],
            "contacts": [mc._plain(c) for c in contacts]}


# ── the golden ───────────────────────────────────────────────────────────────────────────────────────────────────

def load_golden(directory: str | Path) -> dict:
    """Verify the whole bundle (exact file set, manifest, every digest) and load it; a tampered golden is refused, never compared against."""
    directory = Path(directory)
    receipt = mc.verify_bundle(directory)

    def rows(name):
        return [json.loads(line) for line in (directory / name).read_text(encoding="utf-8").splitlines() if line]

    digests = json.loads((directory / "digests.json").read_text(encoding="utf-8"))
    horizon = digests.get("informational", {}).get("horizon")
    if not isinstance(horizon, list) or len(horizon) != 2:
        raise SliceRefused("golden_horizon_missing")
    return {"receipt": receipt, "records": rows("records.jsonl"), "windows": rows("windows.jsonl"), "contacts": rows("contacts.jsonl"),
            "binding": digests["binding"], "horizon": (_aware(horizon[0]), _aware(horizon[1]))}


# ── the proofs ───────────────────────────────────────────────────────────────────────────────────────────────────

def _cell(row: dict) -> tuple:
    key = json.loads(row["gkey"])
    return key["event_class"], key["path_id"]


def _record_identity(row: dict) -> str:
    """Everything a golden record stores except the per-build record id."""
    return mc.canonical({k: v for k, v in row.items() if k != "record_id"})


def _group(rows: list[dict], cell_of: Callable[[dict], tuple], identity: Callable[[dict], str]) -> dict:
    out: dict = {}
    for row in rows:
        out.setdefault(cell_of(row), []).append(identity(row))
    return {cell: sorted(items) for cell, items in out.items()}


def _window_cell(row: dict) -> tuple:
    return row["event_class"], row["path_id"]


def _contact_id_of(record: dict) -> str | None:
    return json.loads(record["gkey"])["contact_id"]


def equality_proof(golden: dict, sliced: dict, classes: list[str]) -> dict:
    """Unchanged cells byte-identical to the measuring golden: records, windows and the contacts those records reference."""
    problems, cells, compared = [], [], 0
    g_rec = _group([r for r in golden["records"] if _cell(r)[0] in classes], _cell, _record_identity)
    s_rec = _group(sliced["records"], _cell, _record_identity)
    g_win = _group([w for w in golden["windows"] if w["event_class"] in classes], _window_cell, mc.canonical)
    s_win = _group(sliced["windows"], _window_cell, mc.canonical)
    g_contacts = {c["contact_id"]: mc.canonical(c) for c in golden["contacts"]}
    s_contacts = {c["contact_id"]: mc.canonical(c) for c in sliced["contacts"]}
    for cls in sorted(classes):
        for path in ("P1", "P2", "P3", "P4"):
            if cell_expectation(cls, path)["kind"] != "same":
                continue
            cell = (cls, path)
            records_equal, windows_equal = g_rec.get(cell, []) == s_rec.get(cell, []), g_win.get(cell, []) == s_win.get(cell, [])
            cells.append({"event_class": cls, "path_id": path, "golden_records": len(g_rec.get(cell, [])), "slice_records": len(s_rec.get(cell, [])),
                          "golden_windows": len(g_win.get(cell, [])), "slice_windows": len(s_win.get(cell, [])),
                          "records_equal": records_equal, "windows_equal": windows_equal})
            compared += len(g_rec.get(cell, [])) + len(s_rec.get(cell, [])) + len(g_win.get(cell, [])) + len(s_win.get(cell, []))
            if not records_equal:
                problems.append(f"equality_records_differ: {cls}/{path}")
            if not windows_equal:
                problems.append(f"equality_windows_differ: {cls}/{path}")
    same_cells = {(c["event_class"], c["path_id"]) for c in cells}
    referenced = {_contact_id_of(r) for r in sliced["records"] if _cell(r) in same_cells}
    referenced |= {_contact_id_of(r) for r in golden["records"] if _cell(r) in same_cells}
    referenced.discard(None)
    for contact_id in sorted(referenced):
        if contact_id not in g_contacts:
            problems.append(f"equality_contact_missing_in_golden: {contact_id}")
        elif contact_id not in s_contacts:
            problems.append(f"equality_contact_missing_in_slice: {contact_id}")
        elif g_contacts[contact_id] != s_contacts[contact_id]:
            problems.append(f"equality_contact_differs: {contact_id}")
    if not same_cells or compared == 0:
        problems.append("equality_vacuous: no unchanged-cell record or window was compared")
    return {"passed": not problems, "cells": cells, "contacts_compared": len(referenced), "problems": problems}


def noninterference_proof(sliced: dict, classes: list[str], *, default_profile_intact: bool) -> dict:
    """The measuring rules' outputs are untouched by the final rules: changed cells hold only final-version rows, suppressed cells hold none,
    and the default rule profile is still the measuring one after the build."""
    problems = []
    for cls in sorted(classes):
        for path in ("P1", "P2", "P3", "P4"):
            expect = cell_expectation(cls, path)
            if expect["kind"] == "same":
                continue
            rows = [r for r in sliced["records"] if _cell(r) == (cls, path)]
            if expect["kind"] == "suppressed" and rows:
                problems.append(f"noninterference_suppressed_cell_not_empty: {cls}/{path} ({len(rows)} rows)")
            for row in rows:
                version = json.loads(row["gkey"])["rule_version"]
                if expect["kind"] == "final" and version != expect["final_version"]:
                    problems.append(f"noninterference_wrong_rule_version: {cls}/{path} carries {version}, final is {expect['final_version']}")
                    break
    stray = sorted({_cell(r)[0] for r in sliced["records"]} - set(classes))
    if stray:
        problems.append(f"noninterference_class_outside_slice: {stray}")
    if not default_profile_intact:
        problems.append("noninterference_default_profile_changed")
    return {"passed": not problems, "problems": problems}


def default_profile_intact() -> bool:
    """With no profile context active the registry must still be the measuring (1.0.0) catalogue and selection."""
    return (rr.bound_path_refs() == tuple(rr.BOUND_PATH_REFS)
            and all(rr.selected_versions_for("business_launch")[p] == "1.0.0" for p in ("P1", "P2", "P3", "P4")))


# ── P06b ─────────────────────────────────────────────────────────────────────────────────────────────────────────

def p06b_complete(receipt_path: str | Path | None = None, plan_model: str | Path = PLAN_MODEL) -> tuple[bool, str | None]:
    """P06b is complete iff its own plan-model detector holds: the receipt file at the detector's path matches the detector's pattern.
    The pattern is read from the plan model, never copied here."""
    model = json.loads(Path(plan_model).read_text(encoding="utf-8"))
    item = next((i for i in model["items"] if i.get("id") == "P06b"), None)
    detector = (item or {}).get("detector") or {}
    if detector.get("type") != "file_contains" or not detector.get("pattern") or not detector.get("path"):
        return False, "p06b_detector_not_found"
    path = Path(receipt_path) if receipt_path is not None else Path(detector["path"])
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False, "p06b_receipt_missing"
    return (True, None) if re.search(detector["pattern"], text) else (False, "p06b_receipt_malformed")


# ── the verdict ──────────────────────────────────────────────────────────────────────────────────────────────────

def verdict(*, choice: dict, golden: dict, build: dict, sliced: dict, p06b: tuple[bool, str | None]) -> dict:
    """QUALIFIED only when the slice built without a defect, both proofs passed and P06b is complete; anything else is FULL_BUILD_REQUIRED."""
    classes = choice["classes"]
    reasons = [f"build_defect: {d['step']}: {d['defect']}: {d['detail']}" for d in build["defects"]]
    if not build["steps"] and not build["defects"]:
        reasons.append("build_empty: no substep ran")
    equality = equality_proof(golden, sliced, classes)
    nonint = noninterference_proof(sliced, classes, default_profile_intact=default_profile_intact())
    reasons += equality["problems"] + nonint["problems"]
    if not p06b[0]:
        reasons.append(p06b[1] or "p06b_incomplete")
    return {"schema": SCHEMA, "verdict": FULL_BUILD_REQUIRED if reasons else QUALIFIED, "reasons": reasons,
            "classes": classes, "heaviest_class": choice["heaviest"], "class_selection": choice["source"],
            "binding": golden["binding"], "golden_manifest_sha256": golden["receipt"]["manifest_sha256"],
            "horizon": [golden["horizon"][0].isoformat(), golden["horizon"][1].isoformat()],
            "build": {"substeps_run": len(build["steps"]), "defects": build["defects"]},
            "equality": equality, "noninterference": nonint,
            "p06b": {"complete": p06b[0], "reason": p06b[1]},
            "cannot_establish": list(CANNOT_ESTABLISH), "independent_acceptance": None}


# ── command line ─────────────────────────────────────────────────────────────────────────────────────────────────

def _choice_from_args(args) -> dict:
    timings = json.loads(Path(args.timings).read_text(encoding="utf-8")) if args.timings else None
    classes = [c for c in args.classes.split(",") if c] if args.classes else None
    return choose_slice(timings=timings, classes=classes)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("choose", "qualify"):
        p = sub.add_parser(name)
        p.add_argument("--timings", help="J-3c observations (`timings`) or draft report JSON; the heaviest class is read from it")
        p.add_argument("--classes", help="three comma-separated class ids (required until real timings exist)")
    q = sub.choices["qualify"]
    q.add_argument("--golden", required=True)
    q.add_argument("--dsn", required=True, help="the lane database (127.0.0.1:55433)")
    q.add_argument("--chart-id", default="482012f1-710e-4a25-994a-93821f5871aa")
    q.add_argument("--ephe-path", required=True)
    q.add_argument("--p06b-receipt")
    q.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        choice = _choice_from_args(args)
        if args.command == "choose":
            print(mc.canonical(choice))
            return 0
        import psycopg
        golden = load_golden(args.golden)
        with psycopg.connect(args.dsn, autocommit=True, connect_timeout=5) as conn:
            build = build_slice(conn, chart_id=args.chart_id, horizon=golden["horizon"], classes=choice["classes"], ephe_path=args.ephe_path)
            sliced = read_slice(conn, chart_id=args.chart_id, classes=choice["classes"])
        result = verdict(choice=choice, golden=golden, build=build, sliced=sliced, p06b=p06b_complete(args.p06b_receipt))
        with Path(args.output).open("x", encoding="utf-8") as out:        # never replaces reviewed evidence
            out.write(mc.canonical(result) + "\n")
        print(result["verdict"])
        return 0 if result["verdict"] == QUALIFIED else 3
    except (SliceRefused, mc.CaptureRefused, OSError, ValueError, KeyError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
