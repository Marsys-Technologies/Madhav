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
  * equality proof   `equality_proof` (SR-EDGES-PROOF a): for every (class, path) cell whose rule selection is the SAME under both profiles, the
                      slice equals the golden in EVERY stored field except the minted span edges (`t_in` / `t_out` of point contacts, and the
                      support / window endpoints that ARE those edges): ids, counts, ordinals, `t_exact`, `delta_lambda` and the span-contact
                      (ingress) edges bit for bit. Vacuous (nothing compared) = fail.
  * tolerance proof   `tolerance_proof` (SR-EDGES-PROOF b): every minted point-contact edge lies within the contact's own stated `delta_lambda`
                      of an INDEPENDENT ephemeris root (`j4d_edge_root`: pyswisseph, the kernel's flags, no kernel solver code).
  * solver isolation  `solver_isolation_proof` (SR-EDGES-PROOF a, stations / arcs / segments): the golden's point obligations are re-solved on the real
                      arc index with the fixed solver and with the pre-fix edge derivation; only `t_in` / `t_out` may differ, the pre-fix run must
                      reproduce the golden's own contacts, and the arc index (stations, arcs, segments) is fingerprinted before and after.
  * rederived golden  `rederive_golden` / `equality_proof(strict_edges=True)` (SR-EDGES-PROOF c): a golden re-derived locally from the old golden's inputs
                      with the fixed solver; the slice's unchanged cells equal it byte for byte, edges included.
  * certification     `certification_proof`: the build's own certification ran under the STRICT policy (`contact_certify.POLICY_RAISE`, observed at the
                      call, not assumed) and an independent collect-all pass over the built slice counts 0 invented / 0 anomaly stretches.
  * peak windows      `peak_windows_row` (SR-A53-NARROW): windows with peak fields set and `maximise_earliest` edges, both > 0 wherever the result policy
                      admits peaks; 0 there is a defect.
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

(I) INTERPRETATION (SR-EDGES-PROOF a): the support intervals of a point-contact record and the window endpoints are DERIVED from the contact's
`t_in` / `t_out` (record_store.py: `raw_support = (occ.t_in, occ.t_out)`), so an endpoint that coincides with a point contact's own edge IS that edge and is
excluded from the bit comparison (replaced by a symbolic token on both sides, so which edge it is still has to agree); every other endpoint (dasha
cuts, horizon clips, span-contact ingresses) stays bit for bit. The tolerance proof then bounds the edge itself. Alternative: compare supports
byte for byte (rejected: it fails on the very field the ruling says moves).

(I) INTERPRETATION (SR-EDGES-PROOF slice): "chronic_onset, one of illness_acute/surgery, major_loss, plus bereavement" is the four classes
`RULED_SLICE_CLASSES` (illness_acute, the first named); `--classes` still overrides.

Lane database only. Never production; never a commit; the caller owns the connection's database lifecycle.
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import re
import sys
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from services.gochara_kernel import measuring_capture as mc
from services.gochara_kernel import measuring_report as mr
from services.gochara_kernel import near_miss as nm
from services.gochara_kernel import rule_registry as rr

SCHEMA = "ky.j4d_slice_verdict/1"
QUALIFIED = "QUALIFIED"
FULL_BUILD_REQUIRED = "FULL_BUILD_REQUIRED"
SLICE_SIZE = 3
#: SR-EDGES-PROOF: chronic_onset, illness_acute (or surgery), major_loss and bereavement
RULED_SLICE_CLASSES = ("bereavement", "chronic_onset", "illness_acute", "major_loss")
RULED_SOURCE = "SR-EDGES-PROOF"
EDGE_FIELDS = ("t_in", "t_out")        # the minted span edges of a point contact: the only contact fields the final solver moves
POINT_TARGET = "point:"
LANE_PORT = 55433
LANE_DB_NAME = re.compile(r"(?:ky_[a-z0-9_]+|a53t_[a-z0-9_]+)")
GENERATION = "5.0"
REPO = Path(__file__).resolve().parents[4]
NEAR_MISS_MIGRATION = REPO / "platform" / "migrations" / "1308_gochara_near_miss_storage.sql"
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


def choose_slice(*, timings: Any = None, classes: list[str] | tuple[str, ...] | None = None, ruled: bool = False) -> dict:
    """The slice: explicit class ids, or derived from J-3c's real timings. Returns {'classes', 'heaviest', 'costs', 'source'}.

    `ruled` is the SR-EDGES-PROOF slice (`RULED_SLICE_CLASSES` unless `classes` is given): the ruling names the classes, so the slice may hold more than
    three and need not hold the heaviest class by timing (the heaviest is still reported when timings are given)."""
    costs = class_costs(timings) if timings is not None else None
    if ruled and classes is None:
        classes = list(RULED_SLICE_CLASSES)
    if classes is not None:
        chosen = list(classes)
        if len(set(chosen)) != len(chosen) or len(chosen) < SLICE_SIZE or (not ruled and len(chosen) != SLICE_SIZE):
            raise SliceRefused(f"slice_not_three_distinct_classes: {chosen!r}")
        unknown = [c for c in chosen if c not in mr.SCORED_CLASSES]
        if unknown:
            raise SliceRefused(f"slice_class_not_scored: {unknown!r}")
        heaviest = None
        if costs is not None:
            heaviest = _heaviest_first(costs)[0]
            if heaviest not in chosen and not ruled:
                raise SliceRefused(f"slice_misses_heaviest_class: {heaviest!r} not in {chosen!r}")
        return {"classes": sorted(chosen), "heaviest": heaviest, "costs": costs, "source": RULED_SOURCE if ruled else "explicit"}
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


@contextmanager
def observe_build():
    """Record what the build REALLY did, at the call: the certification policy of every `certify_contact_geometry` call and the number of
    `maximise_earliest` calls (one per non-constant objective piece). The module attributes are wrapped for the build and restored; nothing
    is assumed from configuration (N.8: a claim about the policy needs a detector that sees the policy)."""
    from services.gochara_kernel import contact_certify as cc
    from services.gochara_kernel import window_sweep as ws
    observed: dict = {"certification_policies": [], "maximise_earliest_calls": 0}
    real_certify, real_maximise = cc.certify_contact_geometry, ws.maximise_earliest

    def certify(*args, **kwargs):
        observed["certification_policies"].append(kwargs.get("sink_policy", cc.POLICY_RAISE))
        return real_certify(*args, **kwargs)

    def maximise(*args, **kwargs):
        observed["maximise_earliest_calls"] += 1
        return real_maximise(*args, **kwargs)
    cc.certify_contact_geometry, ws.maximise_earliest = certify, maximise
    try:
        yield observed
    finally:
        cc.certify_contact_geometry, ws.maximise_earliest = real_certify, real_maximise


def ensure_near_miss_layer(conn: Any) -> str:
    """'present' | 'applied': the lane carries the near-miss storage (migration 1308) before any substep runs, as the final candidate's database does.

    Without it the writer takes its pre-ND-P2 path (`NearMissStore.layer_present`): the builder stores no near-miss and the class's `verify:` refuses
    the first one ("expected contact ... is not in the ledger") because there is nowhere to keep it, so a slice on such a lane fails for a reason the
    final build does not have (J-4d pre-run F2: 10 stretches of psychological_arc, all rootless positive-clearance near-misses of the natal Moon
    point). The strict certification policy is NOT relaxed: the lane is made faithful instead. The REAL migration file is applied (idempotent,
    CREATE ... IF NOT EXISTS, one transaction, the lane connection only) and the writer's own presence test must then say yes, or the harness refuses."""
    require_lane(conn)
    store = nm.NearMissStore(conn)
    if store.layer_present():
        return "present"
    with conn.transaction():
        conn.execute(NEAR_MISS_MIGRATION.read_text(encoding="utf-8"))
    if not store.layer_present():
        raise SliceRefused("near_miss_layer_not_applied")
    return "applied"


def build_slice(conn: Any, *, chart_id: str, horizon: tuple, classes: list[str], ephe_path: str, birth_params: dict | None = None,
                build_id: str = "j4d-slice", head: tuple | None = None, kinds: tuple | None = None,
                paths: tuple | None = None, on_step: Callable[[str, Any], None] | None = None,
                final_rules: bool = True, result_policy: str | None = None, p1_form_b: bool = False) -> dict:
    """Drive the writer's real plan, restricted to `classes`, under the FINAL rules (or, `final_rules=False`, the measuring rules: the re-derivation of
    the golden), one transaction per substep.

    `conn` must be an autocommit lane connection. `head` / `kinds` / `paths` narrow the class-less substeps and the per-class substep kinds
    and paths (a harness on a stubbed L1 and a pre-built substrate cannot run them all); the lane run leaves all three None. `result_policy` selects the
    generation's numeric result policy (None = `all_null_candidate/1` under the final rules, the writer's own default under the measuring ones). The build is NOT a validated test slice, so the writer certifies under its
    STRICT policy (every invented / anomaly stretch raises). Returns {'steps', 'defects', 'observed', 'near_miss_layer'}; the first raised substep stops the build and is a defect.
    """
    from pipeline.orchestrator.writers import ContextSpec, ka_gochara_v5 as writer_mod

    require_lane(conn)
    layer = ensure_near_miss_layer(conn)
    config = {"chart_id": chart_id, "horizon": tuple(horizon), "ephe_path": ephe_path, "gochara_v5_final_rules": final_rules}
    if result_policy is not None:
        config["result_policy"] = result_policy
    elif final_rules:
        # OD-1 (SR-OD1-NUMERICAL): the writer refuses a final-rules run that names no result policy. This slice lane has always run (and proved) the all-NULL
        # policy, so it now NAMES it; a numerical slice is asked for with `result_policy`.
        config["result_policy"] = "all_null_candidate/1"
    if p1_form_b:
        config["gochara_v5_p1_form_b"] = True
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
    with observe_build() as observed:
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
    return {"steps": steps, "defects": defects, "observed": observed, "near_miss_layer": layer}


def read_slice_raw(conn: Any, *, chart_id: str, classes: list[str], generation: str = GENERATION) -> dict:
    """The slice's stored rows exactly as the golden exporter reads them (raw columns, ordered prerequisites), chart AND generation scoped, slice classes
    only; `contacts` are the ones the slice's records reference. `read_slice` is this in the golden's canonical form."""
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
    return {"records": records, "windows": windows, "contacts": contacts}


def read_slice(conn: Any, *, chart_id: str, classes: list[str], generation: str = GENERATION) -> dict:
    """The slice's stored rows in the golden's own canonical form (measuring_capture), chart AND generation scoped, slice classes only."""
    raw = read_slice_raw(conn, chart_id=chart_id, classes=classes, generation=generation)
    return {"records": [mc.golden_record(r) for r in raw["records"]], "windows": [mc._plain(w) for w in raw["windows"]],
            "contacts": [mc._plain(c) for c in raw["contacts"]]}


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


def _is_point(contact: dict | None) -> bool:
    """A point contact (`point:<lambda>` target): the only kind whose span edges the fixed solver moves. Residence / span contacts take their edges from
    the sign-ingress substrate, which the fix does not touch."""
    return contact is not None and str(contact.get("canonical_target", "")).startswith(POINT_TARGET)


def _edge_token(value: Any, contact: dict | None) -> Any:
    """`value` itself, or the symbol of the point-contact edge it IS (so which edge it is still has to agree, but not where the edge fell)."""
    if _is_point(contact):
        if value == contact["t_in"]:
            return "<t_in>"
        if value == contact["t_out"]:
            return "<t_out>"
    return value


def _record_identity(row: dict, contacts: dict | None = None) -> str:
    """Everything a golden record stores except the per-build record id; with `contacts`, a support endpoint that is the record's own point-contact edge
    is replaced by that edge's symbol (SR-EDGES-PROOF a: the edge is judged by the tolerance proof, not compared)."""
    body = {k: v for k, v in row.items() if k != "record_id"}
    if contacts is not None:
        contact = contacts.get(_contact_id_of(row))
        body["supports"] = [[_edge_token(end, contact) for end in interval] for interval in row["supports"]]
    return mc.canonical(body)


def _group(rows: list[dict], cell_of: Callable[[dict], tuple], identity: Callable[[dict], str]) -> dict:
    out: dict = {}
    for row in rows:
        out.setdefault(cell_of(row), []).append(identity(row))
    return {cell: sorted(items) for cell, items in out.items()}


def _window_cell(row: dict) -> tuple:
    return row["event_class"], row["path_id"]


def _contact_id_of(record: dict) -> str | None:
    return json.loads(record["gkey"])["contact_id"]


def _obligation(contact: dict) -> tuple:
    return contact["body"], contact["relation_kind"], contact["canonical_target"]


def _ordinal_sequences(contacts: dict) -> dict:
    """Per physical object, the contact ids in occurrence order (ordinals are assigned over the t_exact-ordered crossing set, substrate.py header;
    the ordinal itself is inside the id hash). An unset t_exact (a truncated contact) sorts last."""
    out: dict = {}
    for contact_id, c in contacts.items():
        out.setdefault(_obligation(c), []).append((c["t_exact"] is None, c["t_exact"] or "", contact_id))
    return {key: [i for _n, _t, i in sorted(items)] for key, items in out.items()}


def _digest(value: Any) -> str:
    import hashlib
    return hashlib.sha256(mc.canonical(value).encode("utf-8")).hexdigest()[:12]


def _seconds_between(a: str | None, b: str | None) -> float | None:
    if a is None or b is None:
        return None
    return abs((datetime.fromisoformat(a) - datetime.fromisoformat(b)).total_seconds())


def edge_moves(golden_contacts: dict, slice_contacts: dict) -> dict:
    """Before / after figures of the point-contact edges present in both (seconds): the product-precision record SR-EDGES-PROOF asks for."""
    seconds = []
    for contact_id, before in golden_contacts.items():
        after = slice_contacts.get(contact_id)
        if after is None or not _is_point(before) or not _is_point(after):
            continue
        for name in EDGE_FIELDS:
            moved = _seconds_between(before[name], after[name])
            if moved is not None:
                seconds.append(moved)
    seconds.sort()
    median = None if not seconds else (seconds[len(seconds) // 2] if len(seconds) % 2 else 0.5 * (seconds[len(seconds) // 2 - 1] + seconds[len(seconds) // 2]))
    return {"edges": len(seconds), "moved": sum(1 for x in seconds if x > 0), "median_seconds": median, "max_seconds": seconds[-1] if seconds else None}


def equality_proof(golden: dict, sliced: dict, classes: list[str], *, strict_edges: bool = False, all_cells: bool = False) -> dict:
    """Unchanged cells equal to the golden in EVERY stored field except the minted point-contact span edges (SR-EDGES-PROOF a).

    Records (gkey = event class, person, agent, relation, object, role, CONTACT ID, path, rule version, prerequisites in ORDINAL order, frame; admission
    state; operator role; supports), windows and the contacts those records reference are compared. For a point contact every field but `t_in` / `t_out` is
    compared (`t_exact`, `delta_lambda`, the id, the body, relation and target); a span contact (ingress) is compared whole, edges included. Support and window
    endpoints that ARE a point contact's edge are compared by symbol (see the module docstring). Per obligation the contact COUNT and the ID SEQUENCE in
    occurrence order are compared too. `strict_edges=True` is the re-derived-golden comparison (c): same solver, so the edges are compared bit for bit as well.
    `all_cells=True` compares every cell, not only those whose rule selection the final rules leave unchanged (a re-derivation under the MEASURING rules).
    """
    problems, cells, compared = [], [], 0
    g_contacts_all = {c["contact_id"]: c for c in golden["contacts"]}
    s_contacts_all = {c["contact_id"]: c for c in sliced["contacts"]}
    tokens = None if strict_edges else True
    g_rec = _group([r for r in golden["records"] if _cell(r)[0] in classes], _cell, lambda r: _record_identity(r, g_contacts_all if tokens else None))
    s_rec = _group(sliced["records"], _cell, lambda r: _record_identity(r, s_contacts_all if tokens else None))

    def window_edges(records, contacts):
        out: dict = {}
        for r in records:
            contact = contacts.get(_contact_id_of(r))
            if _is_point(contact):
                out.setdefault(_cell(r), set()).update((contact["t_in"], contact["t_out"]))
        return out
    g_edges = window_edges([r for r in golden["records"] if _cell(r)[0] in classes], g_contacts_all)
    s_edges = window_edges(sliced["records"], s_contacts_all)

    def window_identity(row, edges):
        if not tokens:
            return mc.canonical(row)
        mine = edges.get(_window_cell(row), set())
        return mc.canonical({k: ("<edge>" if k in ("lo", "hi") and v in mine else v) for k, v in row.items()})
    g_win = _group([w for w in golden["windows"] if w["event_class"] in classes], _window_cell, lambda w: window_identity(w, g_edges))
    s_win = _group(sliced["windows"], _window_cell, lambda w: window_identity(w, s_edges))
    for cls in sorted(classes):
        for path in ("P1", "P2", "P3", "P4"):
            if not all_cells and cell_expectation(cls, path)["kind"] != "same":
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
    g_ref = {i for r in golden["records"] if _cell(r) in same_cells for i in [_contact_id_of(r)] if i is not None}
    s_ref = {i for r in sliced["records"] if _cell(r) in same_cells for i in [_contact_id_of(r)] if i is not None}
    referenced = g_ref | s_ref
    point_compared = span_compared = 0
    for contact_id in sorted(referenced):
        before, after = g_contacts_all.get(contact_id), s_contacts_all.get(contact_id)
        if before is None:
            problems.append(f"equality_contact_missing_in_golden: {contact_id}")
        elif after is None:
            problems.append(f"equality_contact_missing_in_slice: {contact_id}")
        else:
            exempt = () if strict_edges or not _is_point(before) else EDGE_FIELDS
            if _is_point(before) and not strict_edges:
                point_compared += 1
            else:
                span_compared += 1
            if before["t_exact"] != after["t_exact"]:
                problems.append(f"equality_t_exact_differs: {contact_id}")
            if {k: v for k, v in before.items() if k not in exempt and k != "t_exact"} != {k: v for k, v in after.items() if k not in exempt and k != "t_exact"}:
                problems.append(f"equality_contact_differs: {contact_id}")
    g_set = {i: g_contacts_all[i] for i in g_ref if i in g_contacts_all}
    s_set = {i: s_contacts_all[i] for i in s_ref if i in s_contacts_all}
    g_seq, s_seq = _ordinal_sequences(g_set), _ordinal_sequences(s_set)
    for key in sorted(set(g_seq) | set(s_seq), key=lambda k: _digest(list(k))):
        label = f"{key[0]}/{key[1]}/{_digest(list(key))}"
        if len(g_seq.get(key, [])) != len(s_seq.get(key, [])):
            problems.append(f"equality_contact_count_differs: {label} ({len(g_seq.get(key, []))} vs {len(s_seq.get(key, []))})")
        elif g_seq.get(key) != s_seq.get(key):
            problems.append(f"equality_ordinals_differ: {label}")
    if not same_cells or compared == 0:
        problems.append("equality_vacuous: no unchanged-cell record or window was compared")
    return {"passed": not problems, "cells": cells, "contacts_compared": len(referenced), "point_contacts_edge_exempt": point_compared,
            "contacts_compared_whole": span_compared, "obligations_compared": len(set(g_seq) | set(s_seq)), "strict_edges": strict_edges, "all_cells": all_cells,
            "fields_compared": ("every stored field" if strict_edges else "every stored field except the point-contact edges t_in / t_out and the support / window endpoints that are those edges"),
            "problems": problems}


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


# ── the tolerance proof (SR-EDGES-PROOF b) ───────────────────────────────────────────────────────────────────────

_JD_UNIX = 2440587.5


def _jd(iso: str) -> float:
    return datetime.fromisoformat(iso).timestamp() / 86400.0 + _JD_UNIX


def _levels(body: str, relation: str, target: str) -> list[float]:
    """The candidate ray levels of a point contact, from the INDEPENDENT window verifier's own tables (not the solver's): a conjunction's level is the
    target; an aspect's levels are the target minus each of the body's aspect angles (window_verifier._ASPECT_ANGLES)."""
    from services.gochara_kernel import window_verifier as wv
    lam = float(target[len(POINT_TARGET):]) % 360.0
    angles = (0.0,) if relation == "conjunction" else wv._ASPECT_ANGLES.get(body, ())
    return [(lam - a) % 360.0 for a in angles]


def tolerance_proof(sliced: dict, horizon: tuple, *, ephe_path: str, sky: Any = None) -> dict:
    """Every minted point-contact edge lies within the contact's stated `delta_lambda` of an independent ephemeris root.

    The root is found by `j4d_edge_root` (pyswisseph, the kernel's flags, scan + bisection; no kernel solver code). An edge clipped by the horizon is not a
    band edge and is counted, not judged; a contact with no stated `delta_lambda` cannot be judged and is a problem (an honest null is not a pass)."""
    from services.gochara_kernel import window_verifier as wv
    from scripts.kala_gochara_cutover import j4d_edge_root as er
    sky = sky or er.Sky(ephe_path)
    problems, classes, worst_ratio, worst_seconds = [], Counter(), 0.0, 0.0
    for c in sorted(sliced["contacts"], key=lambda c: c["contact_id"]):
        if not _is_point(c) or c["relation_kind"] not in wv._POINT_ORB_DEG:
            continue
        delta = c.get("delta_lambda")
        levels = _levels(c["body"], c["relation_kind"], c["canonical_target"])
        for name in EDGE_FIELDS:
            instant = c[name]
            if instant is None:
                classes["open_ended"] += 1
            elif datetime.fromisoformat(instant) in horizon:
                classes["horizon_clip"] += 1
            elif delta is None or not delta > 0:
                problems.append(f"tolerance_delta_lambda_missing: {c['contact_id']} {name}")
            elif not levels:
                problems.append(f"tolerance_no_ray_level: {c['contact_id']} {name}")
            else:
                got = er.check_edge(sky, c["body"], _jd(instant), levels, wv._POINT_ORB_DEG[c["relation_kind"]], float(delta))
                classes[got["class"]] += 1
                if got["class"] == "unverified":
                    root = "no independent root bracketed" if got["root_jd"] is None else f"{got['seconds_from_root']:.1f} s from the independent root"
                    problems.append(f"tolerance_edge_off_ephemeris: {c['contact_id']} {name} {got['error_deg'] * 3600:.4f} arcsec from the band edge, "
                                    f"stated delta_lambda {float(delta) * 3600:.4f} arcsec ({root})")
                else:
                    worst_ratio = max(worst_ratio, got["error_deg"] / float(delta))
                    worst_seconds = max(worst_seconds, got["seconds_from_root"])
    checked = classes["orb_edge"] + classes["station_closed"] + classes["unverified"]
    if checked == 0:
        problems.append("tolerance_vacuous: no minted point-contact edge was judged against the ephemeris")
    return {"passed": not problems, "edges_judged": checked, "edge_classes": dict(classes), "max_error_over_delta_lambda": worst_ratio,
            "max_seconds_from_root": worst_seconds, "independent_root": "pyswisseph (SWIEPH, sidereal Lahiri), scan + 60-step bisection; no kernel solver code",
            "problems": problems}


# ── the solver isolation proof (SR-EDGES-PROOF a: stations, arcs, segments) ──────────────────────────────────────

def arc_index_fingerprint(index: Any) -> str:
    """The body's stations, arcs and station-bounded segments as one digest (every instant by its exact float repr)."""
    def arc(a):
        return [a.arc_index, repr(a.start_jd), repr(a.end_jd), repr(a.start_lon_unwrapped), repr(a.end_lon_unwrapped), a.direction, a.wrap_index, list(a.station_bounded)]
    return _digest({"stations": [repr(s) for s in index.stations], "arcs": [arc(a) for a in index.arcs], "segments": [arc(a) for a in index.segments]})


@contextmanager
def prefix_edge_derivation():
    """The pre-fix edge derivation: the Swiss polish of the spline edge 'cannot be found', so the spline edge stands (the fix's own documented fallback,
    and the control tests/l3/gochara/test_j4c_span_edge_polish.py uses). The exact-root refinement (`contacts._refine_root`) is untouched."""
    from services.gochara_kernel import record_store as rs
    real = rs._refine_root

    def lost(*_args, **_kwargs):
        raise ValueError("edge polish disabled (pre-fix control)")
    rs._refine_root = lost
    try:
        yield
    finally:
        rs._refine_root = real


def _occurrence_key(o: Any) -> tuple:
    return (o.contact.contact_id.hex, o.contact.occurrence_ordinal, None if o.t_exact is None else o.t_exact.isoformat(), o.truncated, o.solver_method,
            o.delta_lambda, o.delta_t, o.precision_regime, repr(o.level_deg))


def solver_isolation_proof(golden: dict, classes: list[str], horizon: tuple, *, ephe_path: str, index_for: Callable[[str], Any] | None = None) -> dict:
    """Re-solve the golden's point obligations on the real arc index twice, with the fixed edge derivation and with the pre-fix one.

    The fixed solver may move `t_in` / `t_out` and nothing else: ids, ordinals, `t_exact`, `delta_lambda`, solver method, truncation and level are
    compared occurrence by occurrence, and the arc index (stations, arcs, segments) is fingerprinted before and after. The PRE-FIX run must reproduce the golden's
    own contacts (id, `t_exact`, `t_in`, `t_out`), which ties the comparison to the measuring golden rather than to the code alone."""
    from services.gochara_kernel import record_store as rs
    from services.gochara_kernel import substrate
    index_for = index_for or (lambda body: substrate.production_arc_index(body, ephe_path))
    ids = {_contact_id_of(r) for r in golden["records"] if _cell(r)[0] in classes} - {None}
    wanted = {_obligation(c) for c in golden["contacts"] if c["contact_id"] in ids and _is_point(c) and c["relation_kind"] in rs.POINT_KERNEL_RELATION}
    groups: dict = {}
    for c in golden["contacts"]:                  # every golden contact of a referenced obligation: the solver returns the obligation's whole occurrence set
        if _obligation(c) in wanted:
            groups.setdefault(_obligation(c), []).append(c)
    problems, indexes, before, moved_seconds = [], {}, {}, []
    convention_id = substrate.convention_id_for()
    solved = reproduced = 0
    for (body, relation, target) in sorted(groups, key=lambda k: _digest(list(k))):
        label = f"{body}/{relation}/{_digest([body, relation, target])}"
        if body not in indexes:
            indexes[body] = index_for(body.title())
            before[body] = arc_index_fingerprint(indexes[body])
        edge = SimpleNamespace(transit=True, relation=relation, agent=body,
                               obj=substrate.PhysicalObjectId(body=body, relation_kind=relation, canonical_target=target, convention_id=convention_id))

        def solve():
            occs = rs.solve_point_edges([edge], arc_index_for=lambda b: indexes[body], horizon=horizon, ephe_path=ephe_path, refine=True)[id(edge)]
            return sorted(occs, key=lambda o: (o.t_exact is None, o.t_exact or o.t_in, o.t_in))
        fixed = solve()
        with prefix_edge_derivation():
            control = solve()
        solved += len(fixed)
        if len(fixed) == len(control):
            moved_seconds += [abs((getattr(a, name) - getattr(b, name)).total_seconds()) for a, b in zip(fixed, control) for name in EDGE_FIELDS]
        if [_occurrence_key(o) for o in fixed] != [_occurrence_key(o) for o in control]:
            problems.append(f"isolation_fields_other_than_edges_differ: {label}")
        own = sorted(groups[(body, relation, target)], key=lambda c: (c["t_exact"] is None, c["t_exact"] or "", c["contact_id"]))
        mine = [(str(o.contact.contact_id), None if o.t_exact is None else o.t_exact.isoformat(), o.t_in.isoformat(), o.t_out.isoformat()) for o in control]
        want = [(c["contact_id"], c["t_exact"], c["t_in"], c["t_out"]) for c in own]
        if mine != want:
            problems.append(f"isolation_golden_not_reproduced_by_prefix_derivation: {label} ({len(want)} golden vs {len(mine)} solved)")
        else:
            reproduced += len(want)
    for body, index in indexes.items():
        if arc_index_fingerprint(index) != before[body]:
            problems.append(f"isolation_arc_index_changed: {body}")
    if not groups or solved == 0:
        problems.append("isolation_vacuous: no golden point obligation was re-solved")
    moved_seconds.sort()
    return {"passed": not problems, "obligations": len(groups), "occurrences_solved": solved, "golden_contacts_reproduced_by_prefix": reproduced,
            "edges_fixed_vs_prefix": {"edges": len(moved_seconds), "moved": sum(1 for x in moved_seconds if x > 0),
                                      "max_seconds": moved_seconds[-1] if moved_seconds else None},
            "bodies_fingerprinted": sorted(indexes), "arc_index_fingerprints": {b: before[b] for b in sorted(before)}, "problems": problems}


# ── certification under the STRICT policy ────────────────────────────────────────────────────────────────────────

def count_certification(stretch_sink: list[dict]) -> dict:
    """The certifier's own record kinds over a collect-all pass: how many stretches it read as invented and as anomaly."""
    kinds = Counter(r.get("kind") for r in stretch_sink)
    return {"stretches": len(stretch_sink), "invented": kinds.get("invented", 0), "anomaly": kinds.get("anomaly", 0), "by_kind": dict(kinds)}


def swiss_position_at(ephe_path: str) -> Callable[[str, datetime], float]:
    """The certifier's ephemeris position source: the SWIEPH backend asserted at every probe (the writer's own `position_at`, rebuilt here)."""
    from services.gochara_kernel.knots import calc_sidereal_lon

    def position_at(body: str, t: datetime) -> float:
        lon, retflag = calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + _JD_UNIX, ephe_path)
        if not retflag & 2:
            raise RuntimeError(f"position probe {body}: retflag {retflag} lacks the Swiss bit")
        return lon
    position_at.cache_key = ("swiss", ephe_path)
    return position_at


def measure_certification(conn: Any, *, chart_id: str, classes: list[str], ephe_path: str, generation: str = GENERATION) -> dict:
    """An independent collect-all certification of the BUILT slice (`POLICY_SINK_ALL` over the stored contacts, the reconstruction from the ephemeris
    alone), per class; the counts of invented and anomaly stretches, or `unavailable` when a class cannot be certified."""
    from services.gochara_kernel import contact_certify as cc
    position_at = swiss_position_at(ephe_path)
    per_class, unavailable = {}, {}
    for cls in sorted(classes):
        sink: list = []
        try:
            cc.certify_contact_geometry(conn, chart_id=chart_id, generation=generation, event_class=cls, position_at=position_at,
                                        graze_sink=[], stretch_sink=sink, sink_policy=cc.POLICY_SINK_ALL)
        except Exception as exc:                                                    # noqa: BLE001 — a class that cannot be certified is named, never counted as zero
            unavailable[cls] = f"{type(exc).__name__}: {exc}"
            continue
        per_class[cls] = count_certification(sink)
    return {"per_class": per_class, "unavailable": unavailable}


def certification_proof(observed: dict, measured: dict | None) -> dict:
    """STRICT certification and 0 invented / 0 anomaly (D-CLOUD C-7 / C-11). Two detectors: the policy OBSERVED at every certification call of the build
    (all `raise`, at least one call) and the independent collect-all counts over the built slice (both zero, every class certifiable)."""
    from services.gochara_kernel import contact_certify as cc
    policies = list((observed or {}).get("certification_policies", []))
    problems = []
    if not policies:
        problems.append("certification_not_observed: the build made no certification call")
    elif any(p != cc.POLICY_RAISE for p in policies):
        problems.append(f"certification_not_strict: observed policies {sorted(set(policies))}")
    if measured is None:
        problems.append("certification_not_measured: no independent collect-all pass over the built slice")
        invented = anomaly = None
    else:
        invented = sum(c["invented"] for c in measured["per_class"].values())
        anomaly = sum(c["anomaly"] for c in measured["per_class"].values())
        problems += [f"certification_class_unavailable: {cls}: {why}" for cls, why in sorted(measured["unavailable"].items())]
        if not measured["per_class"] and not measured["unavailable"]:
            problems.append("certification_vacuous: no class was certified")
        if invented:
            problems.append(f"certification_invented: {invented}")
        if anomaly:
            problems.append(f"certification_anomaly: {anomaly}")
    return {"passed": not problems, "policy": cc.POLICY_RAISE if policies and set(policies) == {cc.POLICY_RAISE} else sorted(set(policies)),
            "certification_calls": len(policies), "invented": invented, "anomaly": anomaly,
            "per_class": None if measured is None else measured["per_class"], "problems": problems}


# ── the peak-windows row (SR-A53-NARROW) ─────────────────────────────────────────────────────────────────────────

def peak_windows_row(conn: Any, *, chart_id: str, classes: list[str], observed: dict, generation: str = GENERATION) -> dict:
    """Windows with peak fields set and `maximise_earliest` edges (SR-A53-NARROW 4): both must be > 0 wherever the rules admit a peak, and 0 there is
    a defect, not a pass. Under `all_null_candidate/1` no peak is admitted: the row then reports the counts, `admitted` false, and a peak that is set
    anyway is a defect (migration 1240 forbids it)."""
    from services.gochara_kernel import result_policy as rp
    problems = []
    try:
        policy = rp.manifest_policy(conn, chart_id, generation)
    except rp.ResultPolicyMissing as exc:
        policy = None
        problems.append(f"peak_policy_unreadable: {exc}")
    n_peak = conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s)"
                          " AND (peak_instant IS NOT NULL OR score IS NOT NULL OR objective_value IS NOT NULL)", (chart_id, generation, list(classes))).fetchone()[0]
    n_all = conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = ANY(%s)",
                         (chart_id, generation, list(classes))).fetchone()[0]
    edges = int((observed or {}).get("maximise_earliest_calls", 0))
    admitted = policy == rp.POLICY_QUALIFICATION
    if admitted:
        if n_peak == 0:
            problems.append("peak_windows_zero: no window carries a peak field although window_qualification/1 admits them")
        if edges == 0:
            problems.append("maximise_earliest_edges_zero: the sweep never maximised an objective although window_qualification/1 admits peaks")
    elif policy is not None and n_peak:
        problems.append(f"peak_present_under_{policy}: {n_peak} window(s) carry a peak field")
    return {"passed": not problems, "result_policy": policy, "admitted": admitted, "windows": n_all, "windows_with_peak_fields_set": n_peak,
            "maximise_earliest_edges": edges,
            "edges_are": "calls of window_sweep.maximise_earliest during the build (one per non-constant objective piece)",
            "problems": problems}


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

def verdict(*, choice: dict, golden: dict, build: dict, sliced: dict, p06b: tuple[bool, str | None], tolerance: dict | None = None,
            isolation: dict | None = None, certification: dict | None = None, peak_windows: dict | None = None, rederived: dict | None = None) -> dict:
    """QUALIFIED only when the slice built without a defect and every proof passed and P06b is complete; anything else is FULL_BUILD_REQUIRED.

    The tolerance proof, the solver isolation proof, the certification proof and the peak-windows row are REQUIRED (SR-EDGES-PROOF, SR-A53-NARROW): a proof
    that was not run is a reason, never a pass. The comparison with a locally re-derived golden (`rederived`) is optional and, when given, is required to hold."""
    classes = choice["classes"]
    reasons = [f"build_defect: {d['step']}: {d['defect']}: {d['detail']}" for d in build["defects"]]
    if not build["steps"] and not build["defects"]:
        reasons.append("build_empty: no substep ran")
    equality = equality_proof(golden, sliced, classes)
    nonint = noninterference_proof(sliced, classes, default_profile_intact=default_profile_intact())
    reasons += equality["problems"] + nonint["problems"]
    sections = {"tolerance": tolerance, "solver_isolation": isolation, "certification": certification, "peak_windows": peak_windows}
    for name, section in sections.items():
        if section is None:
            reasons.append(f"{name}_proof_not_run")
        else:
            reasons += section["problems"]
    rederived_equality = None
    if rederived is not None:
        rederived_equality = equality_proof(rederived, sliced, classes, strict_edges=True)
        reasons += [f"rederived_{p}" for p in rederived_equality["problems"]]
    if not p06b[0]:
        reasons.append(p06b[1] or "p06b_incomplete")
    cannot = list(CANNOT_ESTABLISH)
    if rederived is None:
        cannot.append("comparison with a golden re-derived locally from the old golden's inputs (j4d_rederive_golden.py; not supplied to this run)")
    return {"schema": SCHEMA, "verdict": FULL_BUILD_REQUIRED if reasons else QUALIFIED, "reasons": reasons,
            "classes": classes, "heaviest_class": choice["heaviest"], "class_selection": choice["source"],
            "binding": golden["binding"], "golden_manifest_sha256": golden["receipt"]["manifest_sha256"],
            "horizon": [golden["horizon"][0].isoformat(), golden["horizon"][1].isoformat()],
            "build": {"substeps_run": len(build["steps"]), "defects": build["defects"]},
            "equality": equality, "noninterference": nonint, **sections, "rederived_equality": rederived_equality,
            "edge_moves": edge_moves({c["contact_id"]: c for c in golden["contacts"]}, {c["contact_id"]: c for c in sliced["contacts"]}),
            "p06b": {"complete": p06b[0], "reason": p06b[1]},
            "cannot_establish": cannot, "independent_acceptance": None}


# ── command line ─────────────────────────────────────────────────────────────────────────────────────────────────

def _choice_from_args(args) -> dict:
    timings = json.loads(Path(args.timings).read_text(encoding="utf-8")) if args.timings else None
    classes = [c for c in args.classes.split(",") if c] if args.classes else None
    return choose_slice(timings=timings, classes=classes, ruled=args.ruled_slice)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("choose", "qualify"):
        p = sub.add_parser(name)
        p.add_argument("--timings", help="J-3c observations (`timings`) or draft report JSON; the heaviest class is read from it")
        p.add_argument("--classes", help="three comma-separated class ids (required until real timings exist)")
        p.add_argument("--ruled-slice", action="store_true", help="the SR-EDGES-PROOF slice: " + ", ".join(RULED_SLICE_CLASSES) + " (--classes overrides)")
    q = sub.choices["qualify"]
    q.add_argument("--golden", required=True)
    q.add_argument("--dsn", required=True, help="the lane database (127.0.0.1:55433)")
    q.add_argument("--chart-id", default="482012f1-710e-4a25-994a-93821f5871aa")
    q.add_argument("--ephe-path", required=True)
    q.add_argument("--p06b-receipt")
    q.add_argument("--rederived", help="a golden bundle re-derived locally by j4d_rederive_golden.py; the slice's unchanged cells must equal it byte for byte")
    q.add_argument("--result-policy", help="the generation's numeric result policy for the build (the writer's default when absent); window_qualification/1 "
                                           "admits peaks, which the peak-windows row then requires")
    q.add_argument("--p1-form-b", action="store_true", help="SR-B1-Q3C-JOB: select P1@1.3.0 (owner's Form B, Q3(c) side rule) for the build; default = 1.0.0, unchanged")
    q.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        choice = _choice_from_args(args)
        if args.command == "choose":
            print(mc.canonical(choice))
            return 0
        import psycopg
        golden = load_golden(args.golden)
        rederived = load_golden(args.rederived) if args.rederived else None
        with psycopg.connect(args.dsn, autocommit=True, connect_timeout=5) as conn:
            build = build_slice(conn, chart_id=args.chart_id, horizon=golden["horizon"], classes=choice["classes"], ephe_path=args.ephe_path,
                                result_policy=args.result_policy, p1_form_b=args.p1_form_b)
            sliced = read_slice(conn, chart_id=args.chart_id, classes=choice["classes"])
            measured = measure_certification(conn, chart_id=args.chart_id, classes=choice["classes"], ephe_path=args.ephe_path)
            peak = peak_windows_row(conn, chart_id=args.chart_id, classes=choice["classes"], observed=build["observed"])
        result = verdict(choice=choice, golden=golden, build=build, sliced=sliced, p06b=p06b_complete(args.p06b_receipt),
                         tolerance=tolerance_proof(sliced, golden["horizon"], ephe_path=args.ephe_path),
                         isolation=solver_isolation_proof(golden, choice["classes"], golden["horizon"], ephe_path=args.ephe_path),
                         certification=certification_proof(build["observed"], measured), peak_windows=peak, rederived=rederived)
        with Path(args.output).open("x", encoding="utf-8") as out:        # never replaces reviewed evidence
            out.write(mc.canonical(result) + "\n")
        print(result["verdict"])
        return 0 if result["verdict"] == QUALIFIED else 3
    except (SliceRefused, mc.CaptureRefused, OSError, ValueError, KeyError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
