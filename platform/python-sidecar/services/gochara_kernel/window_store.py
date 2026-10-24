"""Persistence for the window sweep (A5.3 design v1.5) over migration 1156.

`ka_gochara_eval_window` + `ka_gochara_eval_window_record`, written under the chart family key the
caller already holds (nothing here commits, rolls back or locks). One grain = one
(chart × generation × class × path × rule_version): delete-then-insert, REPLACING never accreting
(§N.3); a sealed generation is refused. The window's coverage snapshot is read FROM THE STORED
PARTITION (`stored_coverage_facts_json`), never hand-shaped (N10/N14).

The post-write check recomputes the connected union FROM SQL (`range_agg` over the stored admitted
records' supports) and compares it with what was written — an independent derivation that shares no
code with `window_sweep.union_components`.
"""
from __future__ import annotations

import bisect
import json as _json
import math
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Callable

from . import targets
from .convention import drishti_angles
from .evaluator import record_uuid
from .record_store import RecordStore, pipelined
from .substrate import DB_BODY
from .window_sweep import OperandSource, SweepRecord, WindowDraft, graha_title, jd_ulp_tolerance

_SIGN_DEG = 30.0


def window_uuid(*, chart_id: str, generation: str, event_class: str, path_id: str,
                rule_version: str, interval: tuple) -> object:
    """Deterministic UUIDv8 over the window's natural key (one connected union per grain)."""
    return record_uuid({
        "kind": "eval_window", "chart_id": str(chart_id), "generation": generation,
        "event_class": event_class, "path_id": path_id, "rule_version": rule_version,
        "interval": [interval[0].astimezone(timezone.utc).isoformat(),
                     interval[1].astimezone(timezone.utc).isoformat()],
    })


def _wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def _read_instant(t: datetime, stored: list[datetime]) -> datetime:
    """The instant at which the sign is READ for `t`, under the platform's boundary convention (half-open: the NEW state owns the change instant —
    p1_operands.py BOUNDARIES; SR-OD1 R-2 / SR-H2-1S), the same convention and the same slack as the sweep's support/geometry check
    (`window_sweep._geometry_at_edge`, `jd_ulp_tolerance`). A stored ingress is a Julian-Day double Swiss bisected to 1e-9 d, so it names the true
    sign edge only to one JD-ulp; `t` within one ulp of a stored ingress `c` is therefore read one ulp INSIDE the state that owns it:
    `t` in `[c, c + ulp)` reads at `c + ulp` (the new sign owns `c`), `t` in `[c - ulp, c)` reads at `c - ulp` (the old sign). Never looser: a stored edge
    further than one ulp from the true one is still read as the wrong sign at its own piece, which the solver's H2 detector refuses. The read never
    leaves the state (clamped to the midpoint to the neighbouring stored ingress when the state is shorter than 2 ulp)."""
    i = bisect.bisect_right(stored, t)                 # stored[i-1] <= t < stored[i]
    if i > 0:
        c = stored[i - 1]
        tol = jd_ulp_tolerance(c)
        if t < c + tol:
            far = c + tol if i == len(stored) else min(c + tol, c + (stored[i] - c) / 2)
            return far
    if i < len(stored):
        c = stored[i]
        tol = jd_ulp_tolerance(c)
        if t >= c - tol:
            return c - tol if i == 0 else max(c - tol, c - (c - stored[i - 1]) / 2)
    return t


def _aspect_offset_provider(target: str, agent: str, position_at: Callable[[str, datetime], float],
                            ingresses: list[datetime] | None = None):
    """Inclusive whole-sign house offset of the target from the aspecting graha's sign at t. `ingresses` = the body's STORED sign-ingress instants
    (ascending); when given, the sign is read under the boundary convention at those edges (`_read_instant`) — absent, at `t` itself."""
    if target.startswith("span:"):
        tgt_sign = targets.span_sign_index(target) - 1
    elif target.startswith("point:"):
        tgt_sign = int(float(target[len("point:"):]) // _SIGN_DEG) % 12
    else:
        return None

    name = graha_title(agent)
    stored = sorted(ingresses) if ingresses else []

    def offset(t: datetime) -> int:
        src_sign = int(position_at(name, _read_instant(t, stored) if stored else t) // _SIGN_DEG) % 12
        return (tgt_sign - src_sign) % 12 + 1

    return offset


# ── the pre-insert mirror of `kgew_qualification_shape_ck` (SR-KGEW-QUAL-BOUND ruling 5) ───────────────────────────────────────────────────────────
# `ka_gochara_window_qualification_ok` (migrations 1240 + 1402) and `ka_gochara_solver_certificate_ok` (1402), restated in Python so that a window the database
# would refuse is a loud named DEFECT BEFORE the row is sent (the constraint failing mid-grain names a constraint, never the window), and measured on its OWN code: the
# builder's fit (`window_solver.stored_certificate`) shares nothing with this check, so a builder miscount cannot pass its own detector. Reachable only through a builder
# defect — `stored_certificate` fits the shape by construction — which is exactly what makes a hit worth raising.
_QUAL_KEYS = ("policy", "unqualified_reason", "unresolved", "affected_channels", "members", "qualified_members")
_QUAL_OPTIONAL = ("combustion_inheritance", "certificate", "solver_certificate")
_QUAL_POLICIES = ("all_null_candidate/1", "window_qualification/1")
_CHANNELS = ("evidence_for_occurrence", "evidence_against_occurrence")
_COMBUSTION_KEYS = ("orb_digest", "orb_row_ids", "l1_module", "l1_module_digest")
_CERT_KEYS = ("schema", "objective", "t0", "outcome", "reason", "phase", "value", "instant", "upper_bound", "evals", "max_evals", "budget_scope",
              "limits", "geometry", "geometry_digest", "cells", "open", "open_total", "truncated")
_LIMIT_KEYS = ("QUANT", "TIE", "EPS_M", "TIME_TOL", "LEAF_CURV", "H1_SPACING_S", "h4_used")
_CELL_KINDS = ("piece", "dead", "leaf", "pruned")
#: the database's caps on a stored solver certificate (migration 1402), restated; a test compares them with the function's own source text
CERT_MAX_CELLS, CERT_MAX_OPEN, CERT_MAX_OCTETS = 400, 200, 262144
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def jsonb_octets(value) -> int:
    """`octet_length(value::jsonb::text)`: PostgreSQL prints a jsonb as `{"k": v, "k2": [1, 2]}` (a space after `:` and `,`), every number as a plain-decimal `numeric` (`1e-06` →
    `0.000001`, `1e+22` → 23 digits — `json.dumps` sizes are NOT the database's) and a string with its JSON escapes (everything else as UTF-8 bytes). A non-finite number is
    not jsonb: ValueError. Never below the database's figure for a finite float (a negative zero is one byte more here than there)."""
    if value is None or value is True:
        return 4
    if value is False:
        return 5
    if isinstance(value, int):
        return len(str(value))
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("a non-finite number is not jsonb")
        return len(format(Decimal(repr(value)), "f"))
    if isinstance(value, str):
        return 2 + sum(2 if ch in '"\\\b\f\n\r\t' else 6 if ord(ch) < 0x20 else len(ch.encode("utf-8")) for ch in value)
    if isinstance(value, (list, tuple)):
        return 2 + sum(jsonb_octets(v) for v in value) + 2 * max(0, len(value) - 1)
    if isinstance(value, dict):
        return 2 + sum(jsonb_octets(k) + 2 + jsonb_octets(v) for k, v in value.items()) + 2 * max(0, len(value) - 1)
    raise TypeError(f"{type(value).__name__} is not jsonb")


def solver_certificate_defects(c) -> list[str]:
    """What `ka_gochara_solver_certificate_ok(c)` would refuse in `c`, as short counts-only phrases (no chart value, no date). [] = the database accepts it."""
    if not isinstance(c, dict):
        return ["the solver certificate is not an object"]
    out: list[str] = []
    if set(c) != set(_CERT_KEYS):
        out.append(f"certificate keys differ from the closed list (missing {sorted(set(_CERT_KEYS) - set(c))}, extra {sorted(set(c) - set(_CERT_KEYS))})")
        return out
    if c["schema"] != "window_solver_certificate/1":
        out.append("schema is not window_solver_certificate/1")
    if c["objective"] not in ("sum_of_group_max", "min_of_group_max"):
        out.append("objective is not a named objective")
    if not isinstance(c["t0"], str):
        out.append("t0 is not a string")
    if c["outcome"] not in ("solved", "blank"):
        out.append("outcome is neither solved nor blank")
    if not (c["reason"] is None or isinstance(c["reason"], str)):
        out.append("reason is neither a string nor null")
    solved = c["outcome"] == "solved"
    if solved != (c["reason"] is None):
        out.append("reason is null iff the outcome is solved — violated")
    if not isinstance(c["phase"], str):
        out.append("phase is not a string")
    for k in ("value", "instant", "upper_bound"):
        if not (c[k] is None or _is_num(c[k])):
            out.append(f"{k} is neither a number nor null")
    if solved != (c["value"] is not None):
        out.append("value is non-null iff the outcome is solved — violated")
    for k in ("evals", "max_evals", "open_total"):
        if not _is_num(c[k]):
            out.append(f"{k} is not a number")
    if c["budget_scope"] != "window":
        out.append("budget_scope is not window")
    lim = c["limits"]
    if not isinstance(lim, dict) or any(k not in lim for k in _LIMIT_KEYS) or not isinstance(lim.get("h4_used"), bool):
        out.append("limits is not an object carrying the required members (h4_used boolean)")
    g = c["geometry"]
    if not isinstance(g, dict) or not isinstance(g.get("cuts"), list) or not isinstance(g.get("pieces"), list):
        out.append("geometry is not an object with cuts and pieces arrays")
    if not (isinstance(c["geometry_digest"], str) and _DIGEST.match(c["geometry_digest"])):
        out.append("geometry_digest is not 64 lowercase hex characters")
    cells, opens = c["cells"], c["open"]
    if not isinstance(cells, list):
        out.append("cells is not an array")
    else:
        if len(cells) > CERT_MAX_CELLS:
            out.append(f"{len(cells)} cells exceed the cap of {CERT_MAX_CELLS}")
        bad = sum(1 for e in cells if not (isinstance(e, list) and len(e) == 4 and e[0] in _CELL_KINDS and all(_is_num(x) for x in e[1:])))
        if bad:
            out.append(f"{bad} malformed cell(s)")
    if not isinstance(opens, list):
        out.append("open is not an array")
    else:
        if len(opens) > CERT_MAX_OPEN:
            out.append(f"{len(opens)} open cells exceed the cap of {CERT_MAX_OPEN}")
        bad = sum(1 for e in opens if not (isinstance(e, list) and len(e) == 2 and all(_is_num(x) for x in e)))
        if bad:
            out.append(f"{bad} malformed open cell(s)")
    if not isinstance(c["truncated"], bool):
        out.append("truncated is not a boolean")
    try:
        n = jsonb_octets(c)
    except (ValueError, TypeError) as exc:
        out.append(f"the certificate is not representable as jsonb ({exc})")
    else:
        if n > CERT_MAX_OCTETS:
            out.append(f"{n} bytes as jsonb text exceed the cap of {CERT_MAX_OCTETS}")
    return out


def qualification_shape_defects(q) -> list[str]:
    """What `kgew_qualification_shape_ck` (`ka_gochara_window_qualification_ok(q)`) would refuse in the window's `qualification` — counts-only phrases; [] = accepted."""
    if q is None:
        return []
    if not isinstance(q, dict):
        return ["the qualification is not an object"]
    out: list[str] = []
    missing = [k for k in _QUAL_KEYS if k not in q]
    extra = sorted(set(q) - set(_QUAL_KEYS) - set(_QUAL_OPTIONAL))
    if missing or extra:
        out.append(f"qualification keys differ from the closed list (missing {missing}, extra {extra})")
        return out
    if q["policy"] not in _QUAL_POLICIES:
        out.append("policy is not a named policy")
    if not (q["unqualified_reason"] is None or isinstance(q["unqualified_reason"], str)):
        out.append("unqualified_reason is neither a string nor null")
    if not isinstance(q["unresolved"], dict) or not all(_is_num(v) for v in q["unresolved"].values()):
        out.append("unresolved is not an object of numbers")
    if not isinstance(q["affected_channels"], list) or any(ch not in _CHANNELS for ch in q["affected_channels"]):
        out.append("affected_channels is not an array of the two channel names")
    if not (_is_num(q["members"]) and _is_num(q["qualified_members"])):
        out.append("members / qualified_members are not numbers")
    if "combustion_inheritance" in q:
        ci = q["combustion_inheritance"]
        if not (isinstance(ci, dict) and set(ci) == set(_COMBUSTION_KEYS) and all(isinstance(ci[k], str) for k in ("orb_digest", "l1_module", "l1_module_digest"))
                and isinstance(ci["orb_row_ids"], dict) and all(_is_num(v) for v in ci["orb_row_ids"].values())):
            out.append("combustion_inheritance is not the closed {orb_digest, orb_row_ids, l1_module, l1_module_digest} record")
    if "certificate" in q and not isinstance(q["certificate"], dict):
        out.append("certificate is not an object")
    if "solver_certificate" in q:
        out += solver_certificate_defects(q["solver_certificate"])
    return out


class QualificationShapeDefect(RuntimeError):
    """A window's `qualification` would violate `kgew_qualification_shape_ck`. Names the window (its deterministic id and grain) and what is wrong — ids and counts only, never a
    chart value or a date. Raised BEFORE the insert: the builder emitted a record the schema's own rule refuses (a builder defect, not data)."""

    def __init__(self, *, window_key: str, event_class: str, path_id: str, rule_version: str, problems: list[str]):
        self.window_key, self.event_class, self.path_id, self.rule_version, self.problems = window_key, event_class, path_id, rule_version, list(problems)
        super().__init__(f"DEFECT: ka_gochara_eval_window.qualification would violate kgew_qualification_shape_ck — window {window_key} "
                         f"(class {event_class}, path {path_id}, rule_version {rule_version}): " + "; ".join(problems))


class WindowStore:
    def __init__(self, conn):
        self.conn = conn
        self._records = RecordStore(conn)

    # ── read ────────────────────────────────────────────────────────────────

    def _fetch_stations(self, body: str, convention_id: str) -> list[datetime]:
        """The substrate's STORED station instants of `body` (the ephemeris-refined `t_exact`, ascending). P1's Mercury / Venus combustion
        reads the retrograde regime from them (L1 gives those two a smaller orb while retrograde). A READ for the window stage, kept here and
        not on `RecordStore` so the geometry implementation identity (and the pin that binds it) does not move for it."""
        rows = self.conn.execute(
            "SELECT t_exact FROM public.ka_gochara_sky_event WHERE event_kind = 'station' AND body = %s"
            " AND convention_id = %s AND t_exact IS NOT NULL ORDER BY t_exact",
            (DB_BODY.get(body, body.lower()), convention_id)).fetchall()
        return [r[0] if not isinstance(r, dict) else next(iter(r.values())) for r in rows]

    def read_grain(self, *, chart_id: str, generation: str, event_class: str, path_id: str,
                   rule_version: str,
                   position_at: Callable[[str, datetime], float] | None = None,
                   p1=None, speed_at: Callable[[str, datetime], tuple] | None = None) -> list[SweepRecord]:
        """The grain's records as sweep inputs. `p1` (a `p1_operands.P1Operands`, bound by the writer only when the P1 operand sources are
        bound) adds the P1 factors' per-factor sources to the P1 records; absent, the records are exactly what they were.

        `speed_at(body, t) -> (longitude, speed deg/day)` (S3, the solver's seam: ONE ephemeris call for both) rides on every record with a body longitude;
        the stored Swiss station instants of the body ride on every POINT-contact record (`station_instants`, the solver's extra cuts, S0 K-2)."""
        anchor_col = "NULL::text"
        if p1 is not None and path_id == "P1":
            if not self._records.p1_anchor_columns_available():
                # without the anchor a delivery form (Sun / Jupiter through another lord's sign) would be judged by the WRONG lord's sky
                raise RuntimeError("P1 operand sources need the period-anchor column (migration 1233): not applied — refused, never defaulted to the agent")
            anchor_col = "r.period_anchor_lord"
        rows = self.conn.execute(
            "SELECT r.record_id::text, COALESCE(r.contact_id, r.object_id)::text, r.path_id,"
            " r.rule_version, r.relation, r.object_kind, r.agent, r.operator_role,"
            " r.admission_state, o.canonical_target, r.house_from_frame,"
            " lower(s.x), upper(s.x), lower_inc(s.x), upper_inc(s.x), c.t_exact, c.convention_id, " + anchor_col +
            " FROM public.ka_gochara_relationship_record r"
            " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id"
            " LEFT JOIN public.ka_gochara_contact c ON (c.chart_id, c.generation, c.contact_id)"
            "                                      = (r.chart_id, r.generation, r.contact_id)"
            " LEFT JOIN LATERAL unnest(r.temporal_support_intervals) AS s(x) ON true"
            " WHERE r.chart_id = %s AND r.generation = %s AND r.event_class = %s"
            " AND r.path_id = %s AND r.rule_version = %s"
            " ORDER BY r.record_id, lower(s.x)",
            (chart_id, generation, event_class, path_id, rule_version)).fetchall()
        grouped: dict[str, dict] = {}
        for (rid, root, pid, ver, rel, kind, agent, role, adm, target, house,
             lo, hi, lo_inc, hi_inc, t_exact, conv, anchor) in rows:
            g = grouped.setdefault(rid, {
                "root": root, "pid": pid, "ver": ver, "rel": rel, "kind": kind, "agent": agent,
                "role": role, "adm": adm, "target": target, "house": house,
                "t_exact": t_exact, "conv": conv, "anchor": anchor, "supports": []})
            if lo is not None:
                if not (lo_inc and not hi_inc):
                    raise RuntimeError(
                        f"record {rid}: support interval bounds are not half-open [lo, hi) — "
                        "the sweep refuses to guess")
                g["supports"].append((lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)))
        out: list[SweepRecord] = []
        crossings: dict[tuple, list[datetime]] = {}
        station_lists: dict[tuple, list[datetime]] = {}

        def stations_of(lord: str, conv: str) -> list[datetime]:
            if (lord, conv) not in station_lists:
                station_lists[(lord, conv)] = sorted(self._fetch_stations(lord, conv))
            return station_lists[(lord, conv)]
        # R8-6: the ingress boundaries are complete over a support only when the class's coverage partition
        # completed that stretch (an incompletely searched stretch may hide an unlisted sign change)
        cov = self.conn.execute(
            "SELECT completed_horizon FROM public.kala_gochara_coverage WHERE chart_id = %s AND generation = %s"
            " AND partition_kind = 'event_class' AND partition_key = %s", (chart_id, generation, event_class)).fetchone()
        completed = None if cov is None else (cov[0] if not isinstance(cov, dict) else next(iter(cov.values())))
        for rid, g in grouped.items():
            lon = offset = rays = hints = bounds = lon_speed = tent_stations = None
            if position_at is not None and g["rel"] in ("residence", "aspect", "conjunction"):
                name = graha_title(g["agent"])
                lon = (lambda t, _n=name: position_at(_n, t))
                rays = drishti_angles(name) if g["rel"] == "aspect" else ()
                if speed_at is not None:
                    lon_speed = (lambda t, _n=name: speed_at(_n, t))
                if g["rel"] in ("conjunction", "aspect") and g["target"].startswith("point:") and g["conv"]:
                    tent_stations = (lambda _n=name, _c=g["conv"]: stations_of(_n, _c))
            if position_at is not None and g["rel"] == "aspect":
                # the dṛṣṭi offset (a house-offset STEP function) changes only where the body changes
                # sign: the exact ingress instants inside the support are the state boundaries
                key = (g["agent"], g["conv"])
                if key not in crossings:
                    crossings[key] = sorted(c.t for c in self._records.fetch_crossings(g["agent"], g["conv"])) \
                        if g["conv"] else []
                # the sign is read at those stored edges under the half-open boundary convention at JD-ulp precision (a stored ingress names the
                # true sign edge only to one ulp; a zero-slack read at it saw the OLD sign on the new state's first instant → H2 blank)
                offset = _aspect_offset_provider(g["target"], g["agent"], position_at, crossings[key])
                bounds = (lambda lo, hi, _c=crossings[key]: [c for c in _c if lo < c < hi])
            if g["t_exact"] is not None and g["rel"] in ("conjunction", "aspect") \
                    and g["target"].startswith("point:"):
                te = g["t_exact"].astimezone(timezone.utc)
                hints = (lambda lo, hi, _te=te: [_te] if lo <= _te < hi else [])
            # the completeness of the ingress list over this record's supports (R8-6, above)
            bounds_complete = bounds is not None and completed is not None and bool(g["supports"]) \
                and all(completed.lower <= a and b <= completed.upper for a, b in g["supports"])
            rec = SweepRecord(
                record_id=rid, root_id=g["root"], path_id=g["pid"], rule_version=g["ver"],
                relation=g["rel"], object_kind=g["kind"], agent=g["agent"],
                operator_role=g["role"], admission_state=g["adm"],
                supports=tuple(g["supports"]), longitude_at=lon, aspect_rays=rays or (),
                aspect_offset_at=offset, house_from_frame=g["house"], canonical_target=g["target"],
                state_boundaries=bounds, peak_hints=hints, state_boundaries_complete=bounds_complete,
                period_anchor_lord=g["anchor"],
                longitude_speed_at=lon_speed, station_instants=tent_stations,
                # W0: the same boundaries, now also stated PER FACTOR — they are the dṛṣṭi offset's, and say nothing
                # about any other state-valued factor of the record
                operand_sources={} if bounds is None else {
                    "graduated_drishti": OperandSource(boundaries=bounds, complete=bounds_complete)})
            if p1 is not None and g["pid"] == "P1":
                # P1a: the period lord's dignity / combustion / maitrī sources. Complete only where the class's coverage partition
                # completed every support (the stored stations behind a Mercury / Venus retrograde regime are a stored list, R8-6).
                lord = graha_title(g["anchor"] or g["agent"])
                stations = None
                if p1.needs_stations(lord) and g["conv"]:
                    stations = stations_of(lord, g["conv"])
                p1_complete = completed is not None and bool(g["supports"]) \
                    and all(completed.lower <= a and b <= completed.upper for a, b in g["supports"])
                rec = p1.attach(rec, complete=p1_complete, stations=stations, event_class=event_class)
            out.append(rec)
        return out

    # ── write ───────────────────────────────────────────────────────────────

    def provenance_columns_available(self) -> bool:
        """Does the APPLIED schema carry the window provenance columns (1240)? Read, never assumed."""
        row = self.conn.execute(
            "SELECT count(*) FROM pg_attribute WHERE attrelid = 'public.ka_gochara_eval_window'::regclass"
            " AND attname IN ('objective', 'objective_value', 'qualification') AND NOT attisdropped").fetchone()
        return (next(iter(row.values())) if isinstance(row, dict) else row[0]) == 3

    def replace_grain_windows(self, *, chart_id: str, generation: str, event_class: str,
                              path_id: str, rule_version: str,
                              drafts: list[WindowDraft]) -> dict[str, int]:
        self._records._refuse_if_sealed(chart_id, generation,
                                        f"window grain {event_class}/{path_id}")
        grain = (chart_id, generation, event_class, path_id, rule_version)
        deleted = self.conn.execute(
            "DELETE FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s"
            " AND event_class = %s AND path_id = %s AND rule_version = %s", grain).rowcount
        if not drafts:
            return {"windows": 0, "memberships": 0, "replaced": deleted}
        coverage_facts = self._records.stored_coverage_facts_json(
            chart_id=chart_id, generation=generation, event_class=event_class)
        provenance = self.provenance_columns_available()
        memberships = 0
        wids = [window_uuid(chart_id=chart_id, generation=generation, event_class=event_class, path_id=path_id, rule_version=rule_version, interval=d.interval)
                for d in drafts]
        quals: list = [None] * len(drafts)
        if provenance:
            # SR-KGEW-QUAL-BOUND (5): every window's qualification is checked against the constraint's own rule BEFORE any insert goes out (a hit is a loud, named defect)
            for i, d in enumerate(drafts):
                quals[i] = d.qualification()
                problems = qualification_shape_defects(quals[i])
                if problems:
                    raise QualificationShapeDefect(window_key=str(wids[i]), event_class=event_class, path_id=path_id, rule_version=rule_version, problems=problems)
        # J-4c: every window and membership insert of the grain goes out together (no statement reads another's result)
        with pipelined(self.conn):
            for d, wid, qual in zip(drafts, wids, quals):
                rng = f"[{d.interval[0].isoformat()},{d.interval[1].isoformat()})"
                base = (str(wid), chart_id, event_class, generation, path_id, rule_version, rng,
                        d.peak_instant, d.score, d.evidence_for, d.evidence_against,
                        d.outcome_valence_for_native, d.severity, event_class, coverage_facts,
                        list(d.null_states_used))
                if provenance:       # R8-4 (1240): the objective, its value and the structured qualification provenance
                    self.conn.execute(
                        "INSERT INTO public.ka_gochara_eval_window ("
                        " window_id, chart_id, event_class, generation, path_id, rule_version, interval,"
                        " peak_instant, score, evidence_for, evidence_against,"
                        " outcome_valence_for_native, severity, coverage_partition_kind,"
                        " coverage_partition_key, coverage_facts, null_states_used,"
                        " objective, objective_value, qualification)"
                        " VALUES (%s,%s,%s,%s,%s,%s,%s::tstzrange,%s,%s,%s,%s,%s,%s,'event_class',%s,"
                        " %s::jsonb,%s::text[],%s,%s,%s::jsonb)",
                        base + (d.objective, d.objective_value, _json.dumps(qual, sort_keys=True)))
                else:
                    self.conn.execute(
                        "INSERT INTO public.ka_gochara_eval_window ("
                        " window_id, chart_id, event_class, generation, path_id, rule_version, interval,"
                        " peak_instant, score, evidence_for, evidence_against,"
                        " outcome_valence_for_native, severity, coverage_partition_kind,"
                        " coverage_partition_key, coverage_facts, null_states_used)"
                        " VALUES (%s,%s,%s,%s,%s,%s,%s::tstzrange,%s,%s,%s,%s,%s,%s,'event_class',%s,"
                        " %s::jsonb,%s::text[])", base)
                for rid in d.record_ids:
                    self.conn.execute(
                        "INSERT INTO public.ka_gochara_eval_window_record ("
                        " window_id, record_id, chart_id, generation, event_class, path_id,"
                        " rule_version) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (str(wid), rid, chart_id, generation, event_class, path_id, rule_version))
                    memberships += 1
        return {"windows": len(drafts), "memberships": memberships, "replaced": deleted}

    # ── independent post-write check ───────────────────────────────────────

    def verify_grain(self, *, chart_id: str, generation: str, event_class: str, path_id: str,
                     rule_version: str) -> dict[str, int]:
        """The stored windows must equal the connected components of the prerequisite-satisfied
        support — recomputed here by Postgres `range_agg` over the stored ADMITTED, SCORED records'
        supports (P4: the multirange INTERSECTION of Jupiter's and Saturn's influence unions), not by
        the sweep — and each window's membership must be exactly the admitted scored records whose
        support OVERLAPS it."""
        grain = (chart_id, generation, event_class, path_id, rule_version)
        rec_where = ("r.chart_id = %s AND r.generation = %s AND r.event_class = %s"
                     " AND r.path_id = %s AND r.rule_version = %s"
                     " AND r.admission_state = 'admitted' AND r.operator_role = 'scored'")
        if path_id == "P4":
            union = ("SELECT range_agg(s.x) FILTER (WHERE r.agent = 'jupiter')"
                     " * range_agg(s.x) FILTER (WHERE r.agent = 'saturn') AS m")
        else:
            union = "SELECT range_agg(s.x) AS m"
        expected = self.conn.execute(
            "SELECT lower(c), upper(c) FROM ("
            " SELECT unnest(m) AS c FROM (" + union +
            " FROM public.ka_gochara_relationship_record r,"
            "      LATERAL unnest(r.temporal_support_intervals) AS s(x)"
            " WHERE " + rec_where + ") q) z ORDER BY 1", grain).fetchall()
        stored = self.conn.execute(
            "SELECT lower(interval), upper(interval) FROM public.ka_gochara_eval_window WHERE"
            " chart_id = %s AND generation = %s AND event_class = %s AND path_id = %s"
            " AND rule_version = %s ORDER BY 1", grain).fetchall()
        if [tuple(r) for r in expected] != [tuple(r) for r in stored]:
            raise RuntimeError(
                f"window verification failed {event_class}/{path_id}: stored windows "
                f"{stored!r} != SQL connected components {expected!r}")
        pair_where = ("w.chart_id = %s AND w.generation = %s AND w.event_class = %s"
                      " AND w.path_id = %s AND w.rule_version = %s")
        want_pairs = ("SELECT w.window_id, r.record_id FROM public.ka_gochara_eval_window w"
                      " JOIN public.ka_gochara_relationship_record r"
                      "   ON r.chart_id = w.chart_id AND r.generation = w.generation"
                      "  AND r.event_class = w.event_class AND r.path_id = w.path_id"
                      "  AND r.rule_version = w.rule_version"
                      "  AND r.admission_state = 'admitted' AND r.operator_role = 'scored'"
                      " WHERE " + pair_where +
                      " AND EXISTS (SELECT 1 FROM unnest(r.temporal_support_intervals) x"
                      "             WHERE x && w.interval)")
        have_pairs = ("SELECT m.window_id, m.record_id FROM public.ka_gochara_eval_window_record m"
                      " JOIN public.ka_gochara_eval_window w ON w.window_id = m.window_id"
                      " WHERE " + pair_where)
        missing = self.conn.execute(
            "SELECT count(*) FROM (" + want_pairs + " EXCEPT " + have_pairs + ") z",
            grain + grain).fetchone()[0]
        extra = self.conn.execute(
            "SELECT count(*) FROM (" + have_pairs + " EXCEPT " + want_pairs + ") z",
            grain + grain).fetchone()[0]
        orphans = self.conn.execute(
            "SELECT count(*) FROM public.ka_gochara_relationship_record r WHERE " + rec_where +
            " AND cardinality(r.temporal_support_intervals) > 0"
            " AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_eval_window_record m"
            "                 WHERE m.record_id = r.record_id)", grain).fetchone()[0]
        if missing or extra or orphans:
            raise RuntimeError(
                f"window verification failed {event_class}/{path_id}: {missing} overlapping "
                f"admitted record(s) not members, {extra} non-overlapping/non-admitted member(s), "
                f"{orphans} admitted record(s) in no window")
        return {"windows": len(stored)}


__all__ = ["WindowStore", "window_uuid", "QualificationShapeDefect", "qualification_shape_defects", "solver_certificate_defects", "jsonb_octets"]
