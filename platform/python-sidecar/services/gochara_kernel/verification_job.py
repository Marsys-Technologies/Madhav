"""The separate VERIFICATION JOB (ND-ROLES option A; Codex round 9, R9-6.1) — a pure, connection-taking library.

The orchestrator hands every writer ONE connection, the builder's, and the builder deliberately holds no privilege on
the verification tables. So no build step can record a verification result — by design. Verification is a SEPARATE ACT
after the build, under the verifier's own database identity; until it has run the candidate gate stays closed.

This module holds everything that act does, as functions of an open connection so each refusal and each row is testable
on a disposable database:

  * `check_identity`      — the connection's login proves its own separation (not the builder, not a superuser, no write
                            privilege on any builder-written table, INSERT on the verification tables);
  * `check_preconditions` — REFUSE BY NAME, writing nothing, unless the generation has an UNSEALED candidate manifest,
                            a complete build (derived from the data), unchanged input identity (the independent
                            re-derivation of the manifest vector) and the §4.0 daśā population;
  * `verify_class`        — per event class: the inventory + ledger re-derivation, the P1 record verifiers, the complete
                            contact-geometry certification, and the per-grain window verification; persisting (replace
                            before seal) only when `persist=True`;
  * `run`                 — the whole sequence, ending in the SAME candidate gate the seal uses, and a report.

The writer's own `verify:<class>` step calls `verify_class(..., persist=False)`: the builder keeps its in-build
self-check as a REPORT; it never persists a verification row (it holds no privilege to).

The entry point `pipeline/orchestrator/verification_job.py` is not a registered writer and is not in the build DAG."""
from __future__ import annotations

from typing import Any, Callable

GENERATION = "5.0"

#: process exit codes of the entry point
EXIT_OK, EXIT_REFUSED, EXIT_DISAGREE, EXIT_PRIVILEGE, EXIT_ERROR = 0, 2, 3, 4, 5

#: tables the builder writes: the verifier must hold NO write privilege on any of them (separation, proven by the job
#: itself before it trusts its own login)
BUILDER_TABLES = (
    "ka_gochara_relationship_record", "ka_gochara_record_prerequisite", "ka_gochara_contact", "ka_gochara_eval_window",
    "ka_gochara_eval_window_record", "ka_gochara_search_input_snapshot", "ka_gochara_search_inventory",
    "ka_gochara_search_path_pin", "ka_gochara_search_obligation", "ka_gochara_search_interval",
    "kala_gochara_coverage", "kala_gochara_publication")
#: the two verification tables the verifier writes (and the only ones)
VERIFICATION_TABLES = ("ka_gochara_search_inventory_verification", "ka_gochara_eval_window_verification")
_WRITE = ("INSERT", "UPDATE", "DELETE", "TRUNCATE")


class VerificationRefused(RuntimeError):
    """A precondition or the identity self-check failed: NOTHING was written. `code` is the stable name."""

    def __init__(self, code: str, detail: str, *, exit_code: int = EXIT_REFUSED):
        super().__init__(f"refused:{code} — {detail}")
        self.code, self.detail, self.exit_code = code, detail, exit_code


def _one(row):
    return None if row is None else (next(iter(row.values())) if isinstance(row, dict) else row[0])


# ── identity ─────────────────────────────────────────────────────────────────────────────────────────

def check_identity(conn) -> dict:
    """Refuse unless THIS connection's login is a separate verifier principal. Not a superuser, not the builder (or a
    member of it), no write privilege on any builder-written table, INSERT on the verification tables. The job never
    uses SET ROLE; it proves the identity it was given."""
    who = conn.execute("SELECT current_user, session_user, r.rolsuper FROM pg_roles r WHERE r.rolname = current_user"
                       ).fetchone()
    user, session, superuser = tuple(who.values()) if isinstance(who, dict) else tuple(who)
    if superuser:
        raise VerificationRefused("identity_not_separate", f"{user} is a superuser", exit_code=EXIT_PRIVILEGE)
    is_builder = user == "data_plane_builder" or (
        _role_exists(conn, "data_plane_builder")
        and bool(_one(conn.execute("SELECT pg_has_role(current_user, 'data_plane_builder', 'MEMBER')").fetchone())))
    if is_builder:
        raise VerificationRefused("identity_not_separate", f"{user} is, or is a member of, the builder principal",
                                  exit_code=EXIT_PRIVILEGE)
    held = []
    for table in BUILDER_TABLES:
        if _one(conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{table}",)).fetchone()) is not True:
            continue
        for priv in _WRITE:
            if _one(conn.execute("SELECT has_table_privilege(current_user, %s, %s)", (f"public.{table}", priv)).fetchone()):
                held.append(f"{priv} on {table}")
    if held:
        raise VerificationRefused("identity_not_separate", f"{user} holds write privileges on builder tables: {held}",
                                  exit_code=EXIT_PRIVILEGE)
    missing = [t for t in VERIFICATION_TABLES
               if _one(conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{t}",)).fetchone()) is True
               and not _one(conn.execute("SELECT has_table_privilege(current_user, %s, 'INSERT')",
                                         (f"public.{t}",)).fetchone())]
    if missing:
        raise VerificationRefused("no_verifier_privilege", f"{user} cannot INSERT into {missing}", exit_code=EXIT_PRIVILEGE)
    return {"login": user, "session": session, "separate": True}


def _role_exists(conn, name: str) -> bool:
    return bool(_one(conn.execute("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s)", (name,)).fetchone()))


# ── preconditions ────────────────────────────────────────────────────────────────────────────────────

def check_preconditions(conn, *, chart_id: str, generation: str, classes=None, ephe_path: str | None = None,
                        modules: dict | None = None, path_refs=None, horizon=None) -> dict:
    """REFUSE BY NAME (nothing written) unless the generation can honestly be verified."""
    from . import input_vector as iv
    from . import input_vector_verifier as ivv
    from . import inventory_verifier as inv_v
    pub = conn.execute("SELECT status, input_generation_vector FROM public.kala_gochara_publication"
                       " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if pub is None:
        raise VerificationRefused("no_candidate_manifest", f"generation {generation} has no manifest")
    status, vector = tuple(pub.values()) if isinstance(pub, dict) else tuple(pub)
    if status == "published" or _one(conn.execute("SELECT public.ka_gochara_generation_is_sealed(%s::uuid, %s)",
                                                  (chart_id, generation)).fetchone()):
        raise VerificationRefused("already_sealed", f"generation {generation} is {'published' if status == 'published' else 'sealed'}"
                                  " — a sealed generation is never re-verified")
    found = [_one(r) if not isinstance(r, tuple) else r[0] for r in conn.execute(
        "SELECT event_class FROM public.ka_gochara_search_inventory WHERE chart_id = %s AND generation = %s ORDER BY 1",
        (chart_id, generation)).fetchall()]
    if not found:
        raise VerificationRefused("incomplete_build", "the generation has no search inventory at all")
    wanted = list(classes) if classes else found
    gaps = []
    for cls in wanted:
        row = conn.execute(
            "SELECT i.inventory_digest IS NOT NULL, i.horizon, (SELECT c.completed_horizon FROM public.kala_gochara_coverage c"
            "  WHERE (c.chart_id, c.generation, c.partition_kind, c.partition_key) = (i.chart_id, i.generation,"
            "        'event_class', i.event_class)) FROM public.ka_gochara_search_inventory i"
            " WHERE i.chart_id = %s AND i.generation = %s AND i.event_class = %s", (chart_id, generation, cls)).fetchone()
        if row is None:
            gaps.append(f"{cls}: no inventory")
            continue
        finalised, inv_h, cov_h = tuple(row.values()) if isinstance(row, dict) else tuple(row)
        if not finalised:
            gaps.append(f"{cls}: inventory not finalised")
        elif cov_h is None or not (cov_h.lower <= inv_h.lower and inv_h.upper <= cov_h.upper):
            gaps.append(f"{cls}: the event-class coverage partition did not complete the inventory horizon")
    if gaps:
        raise VerificationRefused("incomplete_build", "; ".join(gaps))
    out = {"classes": wanted, "manifest_status": status}
    if ephe_path is not None and modules is not None:
        vec = vector if isinstance(vector, dict) else __import__("json").loads(vector)
        try:
            ivv.verify_inputs(conn, vec, ephe_path=ephe_path, modules=modules, path_refs=path_refs,
                              jd_range=iv.consumed_jd_range(horizon))
        except RuntimeError as exc:
            raise VerificationRefused("stale_inputs", str(exc)) from exc
        out["inputs"] = "independently re-derived"
    else:
        out["inputs"] = "NOT re-derived (no ephemeris path / module list supplied)"
    try:
        inv_v.validate_consumed_dasha_population(conn, chart_id=chart_id, generation=generation)
    except inv_v.Unverifiable as exc:
        raise VerificationRefused("stale_inputs", f"the consumed daśā population: {exc}") from exc
    return out


__all__ = ["BUILDER_TABLES", "EXIT_DISAGREE", "EXIT_ERROR", "EXIT_OK", "EXIT_PRIVILEGE", "EXIT_REFUSED", "GENERATION",
           "VERIFICATION_TABLES", "VerificationRefused", "check_identity", "check_preconditions"]


class VerificationDisagrees(RuntimeError):
    """An independent verifier DISAGREES with what the builder stored: no row is written for that class/grain; the gate
    stays closed and the process exits 3 with the named problem."""

    def __init__(self, stage: str, detail: str):
        super().__init__(f"{stage}: {detail}")
        self.stage, self.detail = stage, detail


def _sealed_paths(conn) -> list[tuple[str, str]]:
    return sorted((r[0], r[1]) for r in (tuple(x.values()) if isinstance(x, dict) else tuple(x) for x in conn.execute(
        "SELECT path_id, rule_version FROM public.ka_gochara_rule_path_seal").fetchall()))


def _inventory_header(conn, chart_id, generation, event_class):
    row = conn.execute("SELECT lower(horizon), upper(horizon), inventory_digest, ledger_digest"
                       " FROM public.ka_gochara_search_inventory WHERE chart_id = %s AND generation = %s AND event_class = %s",
                       (chart_id, generation, event_class)).fetchone()
    return None if row is None else (tuple(row.values()) if isinstance(row, dict) else tuple(row))


def verify_class(conn, *, chart_id: str, generation: str, event_class: str, position_at, configured_selection: dict,
                 path_rulings: dict, h_unknown: dict, moon_scope_domain: bool, factor_rows_for: Callable,
                 drishti_bound: bool, vedha_bound: bool, persist: bool) -> dict:
    """Everything the independent verifiers say about ONE event class. With `persist=False` (the builder's in-build
    self-check, and `--report-only`) nothing is written. With `persist=True` — the verifier principal's act — the 1206
    inventory-verification row and every included P1–P4 grain's 1240 window-verification row are REPLACED (the caller
    holds the chart lock and the global SHARED key; the write guards refuse after the seal).

    UNVERIFIED (the verifier cannot derive every path) is a RESULT, not an error. Any independent DISAGREEMENT raises
    `VerificationDisagrees` and writes nothing for the class."""
    from . import contact_certify as cc
    from . import inventory_verifier as inv_v
    from . import record_verifier as rv
    from . import window_gate as wg
    from . import window_verifier as wv

    def stage(name, fn):
        try:
            return fn()
        except (VerificationDisagrees, inv_v.Unverifiable):
            raise
        except RuntimeError as exc:
            raise VerificationDisagrees(name, str(exc)) from exc

    header = _inventory_header(conn, chart_id, generation, event_class)
    if header is None or header[2] is None:
        raise VerificationRefused("incomplete_build", f"{event_class}: no finalised inventory")
    lo, hi, stored_digest, stored_ledger = header
    horizon = (lo, hi)
    out: dict[str, Any] = {"event_class": event_class, "persisted": bool(persist)}
    stored_sel = inv_v.stored_selection(conn, chart_id=chart_id, generation=generation, event_class=event_class)
    configured = {p.lower(): v for p, v in configured_selection.items()}
    drift = {p: (v, configured.get(p)) for p, v in stored_sel.items() if configured.get(p) != v}
    if drift:
        raise VerificationDisagrees("selection", f"the stored inventory searched {drift} (stored, configured)")
    try:
        res = inv_v.rederive_inventory_digest(
            conn, chart_id=chart_id, generation=generation, event_class=event_class, sealed_paths=_sealed_paths(conn),
            path_exclusions=path_rulings, h_unknown_exclusion=h_unknown, selected_versions=stored_sel or None)
    except inv_v.Unverifiable as exc:
        return {**out, "status": "UNVERIFIED", "reason": str(exc)}
    if res["digest"] != stored_digest:
        raise VerificationDisagrees("inventory", f"re-derived {res['digest']} != stored {stored_digest}")
    led = stage("ledger", lambda: inv_v.rederive_ledger_digest(
        conn, chart_id=chart_id, generation=generation, event_class=event_class, obligations=res["obligations"],
        capability={"position_probe": True, "arc_index": True, "aspect_span_solver": True,
                    "moon_scope_domain": moon_scope_domain}))
    if led != stored_ledger:
        raise VerificationDisagrees("ledger", f"re-derived {led} != stored {stored_ledger}")
    out["inventory_digest"], out["ledger_digest"] = res["digest"], led
    out["aspect_spans"] = stage("aspect_spans", lambda: inv_v.verify_aspect_span_contacts(
        conn, chart_id=chart_id, generation=generation, obligations=res["obligations"], position_at=position_at,
        horizon=horizon, _cache={}))
    out["geometry"] = stage("contact_geometry", lambda: cc.certify_contact_geometry(
        conn, chart_id=chart_id, generation=generation, event_class=event_class, position_at=position_at))
    pins = [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(
        "SELECT path_id, rule_version FROM public.ka_gochara_search_path_pin WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND disposition = 'included' AND path_id IN ('P1','P2','P3','P4') ORDER BY 1, 2",
        (chart_id, generation, event_class)).fetchall()]
    if any(p == "P1" for p, _v in pins):
        out["p1"] = {
            "support": stage("p1_support", lambda: rv.verify_p1_support(
                conn, chart_id=chart_id, generation=generation, event_class=event_class)),
            "house": stage("p1_house", lambda: rv.verify_p1_house_descriptor(
                conn, chart_id=chart_id, generation=generation, event_class=event_class))}
        if not rv._anchor_columns(conn) or _p1_minting_open(conn, chart_id, generation, event_class):
            out["p1"]["anchors"] = stage("p1_anchors", lambda: rv.verify_p1_anchors(
                conn, chart_id=chart_id, generation=generation, event_class=event_class, position_at=position_at))
    if persist:
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (chart_id,))
        conn.execute("SELECT public.ka_gochara_lock_global_shared()")
        conn.execute("DELETE FROM public.ka_gochara_search_inventory_verification WHERE chart_id = %s AND generation = %s"
                     " AND event_class = %s AND verifier_id = %s AND verifier_version = %s",
                     (chart_id, generation, event_class, inv_v.VERIFIER_ID, inv_v.VERIFIER_VERSION))
        inv_v.write_verification(conn, chart_id=chart_id, generation=generation, event_class=event_class,
                                 rederived_digest=res["digest"])
    snap = _one(conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s"
                             " AND generation = %s", (chart_id, generation)).fetchone())
    windows = []
    for path_id, version in pins:
        grain = dict(chart_id=chart_id, generation=generation, event_class=event_class, path_id=path_id,
                     rule_version=version)
        stage(f"member_support {path_id}", lambda g=grain: wv.verify_member_support(conn, **g))
        stage(f"member_geometry {path_id}", lambda g=grain: wv.verify_member_geometry(conn, position_at=position_at, **g))
        report = stage(f"window_semantics {path_id}", lambda g=grain, p=path_id, v=version: wv.verify_window_semantics(
            conn, factor_rows=factor_rows_for(p, v), drishti_bound=drishti_bound, vedha_bound=vedha_bound, **g))
        entry = {"path_id": path_id, "rule_version": version, "status": report["status"],
                 "policy_version": report["policy_version"], "windows": report["windows"]}
        if persist:
            stage(f"record_verification {path_id}", lambda g=grain, r=report: wg.record_verification(
                conn, report=r, input_digest=snap, **g))
        windows.append(entry)
    out["windows"] = windows
    out["status"] = "VERIFIED" if all(w["status"] == "VERIFIED" for w in windows) else "UNVERIFIED_DYNAMIC"
    return out


def _p1_minting_open(conn, chart_id, generation, event_class) -> bool:
    """P1 anchors are certified when the generation actually holds P1 transit records, or P1 minting is OPEN (the anchor
    columns exist) — with no anchored records and the columns absent the gate was closed and no P1 claim is made."""
    return bool(_one(conn.execute(
        "SELECT count(*) > 0 FROM public.ka_gochara_relationship_record WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND path_id = 'P1' AND contact_id IS NOT NULL", (chart_id, generation, event_class)).fetchone()))


def run(conn, *, chart_id: str, generation: str = GENERATION, classes=None, position_at, ephe_path: str | None = None,
        modules: dict | None = None, path_refs=None, configured_selection_for: Callable, path_rulings: dict,
        h_unknown: dict, moon_scope_domain: bool, factor_rows_for: Callable, drishti_bound: bool, vedha_bound: bool,
        report_only: bool = False, enforce_identity: bool = True) -> dict:
    """The whole sequence. Identity first, then the preconditions (a refusal writes NOTHING), then one transaction per
    class (replace-before-seal), then the SAME candidate gate the seal uses. `enforce_identity=False` is a TEST SEAM for
    fixtures that connect as a superuser; the entry point never passes it."""
    from . import window_gate as wg
    report: dict[str, Any] = {"chart_id": chart_id, "generation": generation, "report_only": report_only, "classes": {}}
    report["identity"] = check_identity(conn) if enforce_identity else {"separate": "NOT CHECKED (test seam)"}
    pre = check_preconditions(conn, chart_id=chart_id, generation=generation, classes=classes, ephe_path=ephe_path,
                              modules=modules, path_refs=path_refs)
    report["preconditions"] = pre
    disagreements = []
    for cls in pre["classes"]:
        try:
            with conn.transaction():
                report["classes"][cls] = verify_class(
                    conn, chart_id=chart_id, generation=generation, event_class=cls, position_at=position_at,
                    configured_selection=configured_selection_for(cls), path_rulings=path_rulings, h_unknown=h_unknown,
                    moon_scope_domain=moon_scope_domain, factor_rows_for=factor_rows_for, drishti_bound=drishti_bound,
                    vedha_bound=vedha_bound, persist=not report_only)
        except VerificationDisagrees as exc:
            report["classes"][cls] = {"event_class": cls, "status": "DISAGREE", "stage": exc.stage, "detail": exc.detail}
            disagreements.append(cls)
    gate = [] if report_only else wg.candidate_gate(conn, chart_id, generation)
    report["gate"] = gate
    verified = [c for c in report["classes"].values() if c.get("status") == "VERIFIED"]
    report["status"] = ("DISAGREE" if disagreements else
                        ("VERIFIED" if not gate and not report_only and len(verified) == len(report["classes"])
                         else "NOT_VERIFIED"))
    report["cockpit"] = (f"VERIFIED (policy {_policy(report)}, {len(verified)} of {len(report['classes'])} classes)"
                         if report["status"] == "VERIFIED" else
                         f"BUILT · NOT VERIFIED · gate CLOSED ({len(gate)} violation(s), {len(disagreements)} disagreement(s))")
    report["exit_code"] = (EXIT_DISAGREE if disagreements else EXIT_OK)
    return report


def _policy(report) -> str:
    for c in report["classes"].values():
        for w in c.get("windows", ()):
            return w["policy_version"]
    return "n/a"


__all__ += ["VerificationDisagrees", "run", "verify_class"]
