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
#: …plus the one table the verifier's `--brief` mode appends to (F-R12-4). The SEALER holds no write on it (its write surface keeps it).
VERIFIER_WRITE_TABLES = VERIFICATION_TABLES + ("ka_gochara_seal_brief",)
_WRITE = ("INSERT", "UPDATE", "DELETE", "TRUNCATE")
#: the L1 tables the independent re-derivations READ (their ACLs belong to the data-plane owner, not to 1241)
L1_READ_TABLES = ("chart_facts", "chart_dashas")


class VerificationRefused(RuntimeError):
    """A precondition or the identity self-check failed: NOTHING was written. `code` is the stable name."""

    def __init__(self, code: str, detail: str, *, exit_code: int = EXIT_REFUSED):
        super().__init__(f"refused:{code} — {detail}")
        self.code, self.detail, self.exit_code = code, detail, exit_code


def _one(row):
    return None if row is None else (next(iter(row.values())) if isinstance(row, dict) else row[0])


# ── identity ─────────────────────────────────────────────────────────────────────────────────────────

def _builder_owner_roles(conn) -> list[str]:
    """The roles that own the Gochara tables (the data-plane owner) — a login that is a member of one can write them all."""
    return [_one(r) if not isinstance(r, tuple) else r[0] for r in conn.execute(
        "SELECT DISTINCT pg_get_userbyid(c.relowner) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace"
        " WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') AND (c.relname LIKE 'ka\\_gochara\\_%' OR"
        " c.relname LIKE 'kala\\_gochara\\_%')").fetchall()]


def _write_surface(conn, role: str, exempt: tuple = VERIFICATION_TABLES) -> list[str]:
    """Every WRITE privilege `role` effectively holds on the builder write surface — table level (INSERT/UPDATE/DELETE/
    TRUNCATE) AND column level (INSERT/UPDATE on any single column: 1242 grants columns, which `has_table_privilege` does not
    see). The surface is every Gochara table except the two verification tables the verifier itself writes."""
    held: list[str] = []
    tables = [(_one(r) if not isinstance(r, tuple) else r[0]) for r in conn.execute(
        "SELECT c.relname FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace"
        " WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') AND (c.relname LIKE 'ka\\_gochara\\_%%' OR"
        " c.relname LIKE 'kala\\_gochara\\_%%') AND c.relname <> ALL(%s) ORDER BY 1", (list(exempt),)).fetchall()]
    for t in tables:
        for priv in _WRITE:
            if _one(conn.execute("SELECT has_table_privilege(%s, %s, %s)", (role, f"public.{t}", priv)).fetchone()):
                held.append(f"{priv} on {t}")
        for (col,) in (tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(
                "SELECT a.attname FROM pg_attribute a WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped"
                " AND (has_column_privilege(%s, a.attrelid, a.attnum, 'INSERT')"
                "   OR has_column_privilege(%s, a.attrelid, a.attnum, 'UPDATE')) ORDER BY a.attnum",
                (f"public.{t}", role, role)).fetchall()):
            privs = [p for p in ("INSERT", "UPDATE") if _one(conn.execute(
                "SELECT has_column_privilege(%s, %s::regclass, %s, %s)", (role, f"public.{t}", col, p)).fetchone())]
            for p in privs:
                if f"{p} on {t}" not in held:                      # a table-level grant already says it
                    held.append(f"{p}({col}) on {t}")
    return held


def check_identity(conn) -> dict:
    """Refuse unless THIS session is a separate verifier principal, judged on BOTH names the session carries:
    `session_user` (the login) and `current_user` (the effective role). Neither may be a superuser, the builder, a member of the
    builder or of any role that OWNS the Gochara tables, and they must be the SAME role — the job never uses SET ROLE, so a
    session whose current role differs from its login is an elevated/impersonated one (a superuser login under a restricted
    role passes a current-role-only test). The effective role must hold NO write privilege — table OR column level — anywhere on
    the builder write surface, INSERT on the verification tables, and SELECT on the L1 tables its derivations read."""
    who = conn.execute("SELECT current_user, session_user").fetchone()
    user, session = tuple(who.values()) if isinstance(who, dict) else tuple(who)
    owners = _builder_owner_roles(conn)
    for label, name in (("session_user", session), ("current_user", user)):
        if _one(conn.execute("SELECT rolsuper FROM pg_roles WHERE rolname = %s", (name,)).fetchone()):
            raise VerificationRefused("identity_not_separate", f"{label} {name} is a superuser", exit_code=EXIT_PRIVILEGE)
        is_builder = name == "data_plane_builder" or (
            _role_exists(conn, "data_plane_builder")
            and bool(_one(conn.execute("SELECT pg_has_role(%s, 'data_plane_builder', 'MEMBER')", (name,)).fetchone())))
        if is_builder:
            raise VerificationRefused("identity_not_separate", f"{label} {name} is, or is a member of, the builder principal",
                                      exit_code=EXIT_PRIVILEGE)
        for owner in owners:
            if name == owner or _one(conn.execute("SELECT pg_has_role(%s, %s, 'MEMBER')", (name, owner)).fetchone()):
                raise VerificationRefused(
                    "identity_not_separate", f"{label} {name} is, or is a member of, {owner}, which OWNS the Gochara tables",
                    exit_code=EXIT_PRIVILEGE)
    if session != user:
        raise VerificationRefused(
            "identity_not_separate", f"session_user {session} differs from current_user {user}: an elevated session (SET ROLE / "
            "impersonation) — the job proves the identity it was LOGGED IN as and never uses SET ROLE", exit_code=EXIT_PRIVILEGE)
    held = _write_surface(conn, user, VERIFIER_WRITE_TABLES)
    if held:
        raise VerificationRefused("identity_not_separate", f"{user} holds write privileges on the builder write surface: {held}",
                                  exit_code=EXIT_PRIVILEGE)
    l1_missing = [t for t in L1_READ_TABLES
                  if _one(conn.execute("SELECT to_regclass(%s) IS NOT NULL", (f"public.{t}",)).fetchone()) is True
                  and not _one(conn.execute("SELECT has_table_privilege(current_user, %s, 'SELECT')",
                                            (f"public.{t}",)).fetchone())]
    if l1_missing:
        raise VerificationRefused(
            "no_verifier_privilege",
            f"verifier lacks SELECT on {'/'.join(l1_missing)} — the L1 read ACLs belong to the data-plane owner and the "
            "verifier/sealer grants migration (1241) does not grant them", exit_code=EXIT_PRIVILEGE)
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

def _enforce_class_census(conn, *, chart_id, generation, vector, found) -> None:
    # G8 (steward GAPS-G8-G9): the CLASS CENSUS. The generation as a whole — not only the classes this run was asked to verify — must
    # claim EXACTLY the scored classes its manifest pins, and the pinned list must be this verifier's own universe (the vector component
    # check in verify_inputs below re-derives that). A claimed class is an event_class coverage partition OR a search inventory; a
    # candidate left with 16 of 26 classes after a failed dispatch, or carrying an unscored one, is refused BY NAME here, before any row
    # is written, and again by the seal-time completeness function (migration 1306).
    _vec0 = vector if isinstance(vector, dict) else __import__("json").loads(vector)
    pinned = _vec0.get("scored_classes")
    if not isinstance(pinned, list) or not pinned:
        raise VerificationRefused("class_census_unpinned", f"the manifest vector of generation {generation} pins no expected class census "
                                  "(scored_classes) — a candidate must say which classes it is built for")
    claimed = sorted(set(found) | {_one(r) if not isinstance(r, tuple) else r[0] for r in conn.execute(
        "SELECT partition_key FROM public.kala_gochara_coverage WHERE chart_id = %s AND generation = %s AND partition_kind = 'event_class'",
        (chart_id, generation)).fetchall()})
    missing, extra = sorted(set(pinned) - set(claimed)), sorted(set(claimed) - set(pinned))
    if missing or extra:
        raise VerificationRefused(
            "class_census_mismatch", f"generation {generation} claims {len(claimed)} class(es) but its manifest pins {len(pinned)}: "
            f"missing {missing or 'none'}; not in the pinned list {extra or 'none'} — a full candidate must claim exactly the scored classes")


def check_preconditions(conn, *, chart_id: str, generation: str, classes=None, ephe_path: str | None = None,
                        modules: dict | None = None, path_refs=None, horizon=None) -> dict:
    """REFUSE BY NAME (nothing written) unless the generation can honestly be verified."""
    from . import input_vector as iv
    from . import input_vector_verifier as ivv
    from . import inventory_verifier as inv_v
    # R10-4 (i): independent input identity is MANDATORY. A run with no ephemeris path or no module map cannot derive the
    # identity of what it verifies; it refuses, naming the gap, before it reads or writes anything.
    if not ephe_path or not modules:
        raise VerificationRefused(
            "no_input_identity", "the independent input identity cannot be derived: "
            + ("no ephemeris path " if not ephe_path else "") + ("no implementation module map " if not modules else "")
            + "was supplied — a verification that cannot re-derive its own inputs persists nothing")
    pub = conn.execute("SELECT status, input_generation_vector, horizon FROM public.kala_gochara_publication"
                       " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if pub is None:
        raise VerificationRefused("no_candidate_manifest", f"generation {generation} has no manifest")
    status, vector, manifest_horizon = tuple(pub.values()) if isinstance(pub, dict) else tuple(pub)
    if status == "published" or _one(conn.execute("SELECT public.ka_gochara_generation_is_sealed(%s::uuid, %s)",
                                                  (chart_id, generation)).fetchone()):
        raise VerificationRefused("already_sealed", f"generation {generation} is {'published' if status == 'published' else 'sealed'}"
                                  " — a sealed generation is never re-verified")
    found = [_one(r) if not isinstance(r, tuple) else r[0] for r in conn.execute(
        "SELECT event_class FROM public.ka_gochara_search_inventory WHERE chart_id = %s AND generation = %s ORDER BY 1",
        (chart_id, generation)).fetchall()]
    if not found:
        raise VerificationRefused("incomplete_build", "the generation has no search inventory at all")
    _enforce_class_census(conn, chart_id=chart_id, generation=generation, vector=vector, found=found)
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
    if manifest_horizon is None:
        raise VerificationRefused("no_input_identity", "the manifest binds no horizon — the consumed ephemeris range "
                                  "cannot be derived")
    vec = vector if isinstance(vector, dict) else __import__("json").loads(vector)
    try:
        ivv.verify_inputs(conn, vec, ephe_path=ephe_path, modules=modules, path_refs=path_refs,
                          jd_range=iv.consumed_jd_range((manifest_horizon.lower, manifest_horizon.upper)),
                          require_scored_classes=True)
    except RuntimeError as exc:
        raise VerificationRefused("stale_inputs", str(exc)) from exc
    out["inputs"] = "independently re-derived"
    # R10-4 (ii): the runner names ITS OWN code — and that code must be the code the manifest vector pinned
    from . import window_gate as wg
    who = conn.execute("SELECT current_user, session_user").fetchone()
    login, session = tuple(who.values()) if isinstance(who, dict) else tuple(who)
    try:
        runner = wg.runner_identity(modules, login=login, session=session)
    except RuntimeError as exc:
        raise VerificationRefused("no_runner_identity", str(exc)) from exc
    import hashlib
    pinned = hashlib.sha256(wg._canon(vec["implementation"]).encode("utf-8")).hexdigest()
    if runner["implementation_digest"] != pinned:
        raise VerificationRefused("runner_not_pinned", f"this runner's implementation digest {runner['implementation_digest']} "
                                  f"is not the one the manifest pinned ({pinned}) — it is not the governed verification job")
    out["runner"] = runner
    try:
        inv_v.validate_consumed_dasha_population(conn, chart_id=chart_id, generation=generation)
    except inv_v.Unverifiable as exc:
        raise VerificationRefused("stale_inputs", f"the consumed daśā population: {exc}") from exc
    return out


__all__ = ["BUILDER_TABLES", "EXIT_DISAGREE", "EXIT_ERROR", "EXIT_OK", "EXIT_PRIVILEGE", "EXIT_REFUSED", "GENERATION",
           "VERIFICATION_TABLES", "VERIFIER_WRITE_TABLES", "VerificationRefused", "check_identity", "check_preconditions"]


class VerificationDisagrees(RuntimeError):
    """An independent verifier DISAGREES with what the builder stored: no row is written for that class/grain; the gate
    stays closed and the process exits 3 with the named problem."""

    def __init__(self, stage: str, detail: str):
        super().__init__(f"{stage}: {detail}")
        self.stage, self.detail = stage, detail


def take_locks(conn, chart_id: str) -> None:
    """R10-3: the chart lock, THEN the global SHARED key — the builder's own order — taken before ANY read that feeds an
    attestation and held (transaction-scoped advisory locks) until the caller's transaction ends. Re-entrant."""
    conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (chart_id,))
    conn.execute("SELECT public.ka_gochara_lock_global_shared()")


def _included_pins(conn, chart_id, generation, event_class):
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(
        "SELECT path_id, rule_version FROM public.ka_gochara_search_path_pin WHERE chart_id = %s AND generation = %s"
        " AND event_class = %s AND disposition = 'included' AND path_id IN ('P1','P2','P3','P4') ORDER BY 1, 2",
        (chart_id, generation, event_class)).fetchall()]


def class_fingerprint(conn, chart_id: str, generation: str, event_class: str) -> dict:
    """R10-3: the exact INPUT/OUTPUT identity one class verification checks — the inventory and ledger digests, and for each
    included grain the digest of its complete semantic dependency set (records, results, contacts, snapshot, manifest,
    policy: `window_gate.derivation_inputs_digest`) and the content digest of its stored windows. Read under the locks at
    the start, re-read before anything persists; a persisted report is bound to it."""
    from . import window_gate as wg
    hdr = _inventory_header(conn, chart_id, generation, event_class)
    fp: dict[str, Any] = {"inventory": None if hdr is None else [hdr[2], hdr[3]], "grains": {}}
    for path_id, version in _included_pins(conn, chart_id, generation, event_class):
        grain = dict(chart_id=chart_id, generation=generation, event_class=event_class, path_id=path_id, rule_version=version)
        content = _one(conn.execute("SELECT public.ka_gochara_eval_window_content_digest(%s::uuid, %s, %s, %s, %s)",
                                    (chart_id, generation, event_class, path_id, version)).fetchone())
        fp["grains"][f"{path_id}@{version}"] = [wg.derivation_inputs_digest(conn, **grain), content]
    return fp


def fingerprint_digest(fp: dict) -> str:
    import hashlib
    from .window_gate import _canon
    return hashlib.sha256(_canon(fp).encode("utf-8")).hexdigest()


def precondition_fingerprint(conn, chart_id: str, generation: str) -> str:
    """The identity of the SHARED preconditions (the manifest vector and status, the snapshot's input identity): re-read under
    the lock by every class transaction and compared with the one the independent input derivation vouched for."""
    import hashlib
    from .window_gate import _canon
    pub = conn.execute("SELECT status, input_generation_vector::text FROM public.kala_gochara_publication"
                       " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    snap = conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s"
                        " AND generation = %s", (chart_id, generation)).fetchone()
    pub = None if pub is None else (tuple(pub.values()) if isinstance(pub, dict) else tuple(pub))
    return hashlib.sha256(_canon({"manifest": None if pub is None else [pub[0], pub[1]],
                                  "input": _one(snap)}).encode("utf-8")).hexdigest()


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
                 drishti_bound: bool, vedha_bound: bool, persist: bool, runner: dict | None = None) -> dict:
    """See `_verify_class`. A class whose records (or any derivation) the verifier cannot independently derive is
    UNVERIFIED — an explicit result, the gate stays closed, nothing is persisted — never a pass."""
    from . import inventory_verifier as inv_v
    try:
        return _verify_class(conn, chart_id=chart_id, generation=generation, event_class=event_class,
                             position_at=position_at, configured_selection=configured_selection,
                             path_rulings=path_rulings, h_unknown=h_unknown, moon_scope_domain=moon_scope_domain,
                             factor_rows_for=factor_rows_for, drishti_bound=drishti_bound, vedha_bound=vedha_bound,
                             persist=persist, runner=runner)
    except inv_v.Unverifiable as exc:
        return {"event_class": event_class, "persisted": False, "status": "UNVERIFIED", "reason": str(exc)}


def _verify_class(conn, *, chart_id: str, generation: str, event_class: str, position_at, configured_selection: dict,
                  path_rulings: dict, h_unknown: dict, moon_scope_domain: bool, factor_rows_for: Callable,
                  drishti_bound: bool, vedha_bound: bool, persist: bool, runner: dict | None = None) -> dict:
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

    # R10-3: protection FIRST — nothing that feeds an attestation is read before the chart and global locks are held
    take_locks(conn, chart_id)
    # R11-1: the GENERATION-WIDE output check — nothing is verified, let alone persisted, while any record/window/membership
    # sits outside the generation's permitted output grains or any result in ANY grain breaks the manifest's policy
    from .result_policy import manifest_policy as _mp
    from . import window_gate as _wg
    wide = _wg.generation_output_problems(conn, chart_id, generation, _mp(conn, chart_id, generation))
    if wide:
        raise VerificationDisagrees("generation_output", "; ".join(wide))
    header = _inventory_header(conn, chart_id, generation, event_class)
    if header is None or header[2] is None:
        raise VerificationRefused("incomplete_build", f"{event_class}: no finalised inventory")
    lo, hi, stored_digest, stored_ledger = header
    horizon = (lo, hi)
    out: dict[str, Any] = {"event_class": event_class, "persisted": bool(persist)}
    fp0 = class_fingerprint(conn, chart_id, generation, event_class)       # the exact data this verification checks
    out["fingerprint"] = fingerprint_digest(fp0)
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
    # R10-6: the fixed 3 s / 6 h aspect-span precheck is GONE — `contact_certify` (next) certifies the aspect-to-span contacts,
    # like every other, under the DERIVED tolerance (accuracy / |speed| + 1 s) and the union-of-contacts contract
    out["geometry"] = stage("contact_geometry", lambda: cc.certify_contact_geometry(
        conn, chart_id=chart_id, generation=generation, event_class=event_class, position_at=position_at))
    from . import record_derivation as rd
    snap_facts = _one(conn.execute("SELECT consumed_fact_ids FROM public.ka_gochara_search_input_snapshot"
                                   " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone())
    chart = inv_v.read_chart(conn, snap_facts) if snap_facts is not None else None
    from .result_policy import manifest_policy
    policy = manifest_policy(conn, chart_id, generation)
    pins = _included_pins(conn, chart_id, generation, event_class)
    if any(p == "P1" for p, _v in pins):
        out["p1"] = {
            "support": stage("p1_support", lambda: rv.verify_p1_support(
                conn, chart_id=chart_id, generation=generation, event_class=event_class)),
            "house": stage("p1_house", lambda: rv.verify_p1_house_descriptor(
                conn, chart_id=chart_id, generation=generation, event_class=event_class))}
        # R10-1: ALWAYS certify the included P1 anchors when the schema exists — an entirely omitted P1 record
        # population is exactly the case the expected-contact derivation exists to catch (the conditional skip,
        # keyed on whether any anchored record SURVIVED, is gone)
        if rv._anchor_columns(conn):
            out["p1"]["anchors"] = stage("p1_anchors", lambda: rv.verify_p1_anchors(
                conn, chart_id=chart_id, generation=generation, event_class=event_class, position_at=position_at))
            p1_version = next(v for p, v in pins if p == "P1")
            out["p1"]["results"] = stage("p1_results", lambda: rd.verify_p1_results(
                conn, chart_id=chart_id, generation=generation, event_class=event_class, rule_version=p1_version,
                chart=chart, policy=policy))
    snap = _one(conn.execute("SELECT input_digest FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s"
                             " AND generation = %s", (chart_id, generation)).fetchone())
    windows = []
    reports: list = []
    for path_id, version in pins:
        grain = dict(chart_id=chart_id, generation=generation, event_class=event_class, path_id=path_id,
                     rule_version=version)
        derived = None
        if path_id != "P1":
            # R10-1: every record the path MUST hold, derived from the obligations × the certified contacts × the bound
            # chart; compared both directions (an empty stored path included); its DERIVED windows feed the gate
            derived = stage(f"records {path_id}", lambda g=grain: rd.verify_path_records(
                conn, obligations=res["obligations"], chart=chart, horizon_hi=hi, policy=policy,
                **{k: g[k] for k in ("chart_id", "generation", "event_class", "path_id", "rule_version")}))
            out.setdefault("records", {})[path_id] = derived["records"]
        stage(f"member_support {path_id}", lambda g=grain: wv.verify_member_support(conn, **g))
        stage(f"member_geometry {path_id}", lambda g=grain: wv.verify_member_geometry(conn, position_at=position_at, **g))
        report = stage(f"window_semantics {path_id}", lambda g=grain, p=path_id, v=version: wv.verify_window_semantics(
            conn, factor_rows=factor_rows_for(p, v), drishti_bound=drishti_bound, vedha_bound=vedha_bound, **g))
        entry = {"path_id": path_id, "rule_version": version, "status": report["status"],
                 "policy_version": report["policy_version"], "windows": report["windows"]}
        windows.append(entry)
        reports.append((grain, report, None if derived is None else derived["derived_windows"]))
    out["windows"] = windows
    if persist:
        # ORDER (Stream B's all-guards rehearsal): the WINDOW verifications first, the 1206 inventory row last — the class's
        # candidate gate refuses until every included grain has a window verification. 1241 gives the verifier SELECT+INSERT
        # on the inventory verification table and NO DELETE: a re-run replaces nothing there (`write_verification` is
        # idempotent for an identical digest, and a rebuilt inventory chain removes its own verification); the 1240 rows are
        # replaced by `record_verification` (the verifier holds DELETE on its own table, pre-seal).
        take_locks(conn, chart_id)                                  # (re-entrant: held since the top)
        fp1 = class_fingerprint(conn, chart_id, generation, event_class)
        if fp1 != fp0:                                              # R10-3: the report must identify the data it checked
            raise VerificationDisagrees(
                "consistency", "the data this verification checked changed before it could be persisted — the report "
                "no longer identifies the stored state (a writer replaced it outside the lock protocol); nothing is persisted")
        for grain, report, derived_w in reports:
            stage(f"record_verification {grain['path_id']}", lambda g=grain, r=report, d=derived_w:
                  wg.record_verification(conn, report=r, input_digest=snap, expected=d, runner=runner,
                                         checked_inputs_digest=fp0["grains"][f"{g['path_id']}@{g['rule_version']}"][0],
                                         **g))
        stage("inventory_verification", lambda: inv_v.write_verification(
            conn, chart_id=chart_id, generation=generation, event_class=event_class, rederived_digest=res["digest"]))
    out["status"] = "VERIFIED" if all(w["status"] == "VERIFIED" for w in windows) else "UNVERIFIED_DYNAMIC"
    return out


#: The arms of the 1206/1232 completeness function that compare the inventory/snapshot with the PUBLISHED manifest row
#: (`... WHERE p.status = 'published'`). On a CANDIDATE manifest — the only kind a verification runs against — that row does not
#: exist, so each reports a spurious violation against NULL. They are RE-EVALUATED here against the candidate manifest itself;
#: nothing else in the combined gate is touched. (Stream B: the function selecting `status IN ('candidate','published')` would
#: make this unnecessary.)
_PUBLISHED_ONLY = (("input_vector_mismatch", None), ("horizon_manifest_mismatch", None),
                   ("convention_bridge_missing", "publication legacy convention"))


def candidate_gate_on_candidate_manifest(conn, chart_id: str, generation: str) -> list[dict]:
    """R10-4 (iii): `ka_gochara_candidate_gate_violations` — the SAME combined gate the seal uses — evaluated on the actual
    candidate manifest. The completeness half reads the manifest only while it is `published`; the three arms that do are
    re-derived against the candidate row (same predicates), everything else is the function's own output verbatim."""
    from . import window_gate as wg
    out = wg.combined_candidate_gate(conn, chart_id, generation)
    pub = conn.execute("SELECT status, horizon, input_generation_vector, convention_id FROM public.kala_gochara_publication"
                       " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    if pub is None:
        return out + [{"event_class": "*", "path_id": None, "rule_version": None, "violation": "no_candidate_manifest",
                       "detail": f"generation {generation} has no manifest"}]
    status, m_horizon, m_vector, m_convention = tuple(pub.values()) if isinstance(pub, dict) else tuple(pub)
    if status == "published":
        return out                                      # the function saw the manifest: its output stands unchanged
    def spurious(v):
        for name, prefix in _PUBLISHED_ONLY:
            if v["violation"] == name and (prefix is None or str(v["detail"]).startswith(prefix)):
                return True
        return False
    out = [v for v in out if not spurious(v)]
    snap = conn.execute("SELECT input_generation_vector, convention_id FROM public.ka_gochara_search_input_snapshot"
                        " WHERE chart_id = %s AND generation = %s", (chart_id, generation)).fetchone()
    snap_vector, snap_convention = (None, None) if snap is None else (tuple(snap.values()) if isinstance(snap, dict) else tuple(snap))
    mk = lambda cls, name, detail: {"event_class": cls, "path_id": None, "rule_version": None, "violation": name,           # noqa: E731
                                    "detail": detail}
    if snap_vector != m_vector:
        out.append(mk("*", "input_vector_mismatch", "snapshot vector differs from the candidate manifest vector"))
    bridge = conn.execute("SELECT sky_convention_id FROM public.ka_gochara_convention_bridge WHERE kala_convention_id = %s",
                          (m_convention,)).fetchone()
    if bridge is None:
        out.append(mk("*", "convention_bridge_missing", f"candidate manifest legacy convention {m_convention}"))
    elif (bridge[0] if not isinstance(bridge, dict) else next(iter(bridge.values()))) != snap_convention:
        out.append(mk("*", "convention_mismatch", f"candidate manifest convention {m_convention} is bridged to a sky "
                                                   f"convention other than the snapshot's {snap_convention}"))
    for (cls, horizon) in (tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(
            "SELECT event_class, horizon FROM public.ka_gochara_search_inventory WHERE chart_id = %s AND generation = %s",
            (chart_id, generation)).fetchall()):
        if horizon != m_horizon:
            out.append(mk(cls, "horizon_manifest_mismatch", f"{horizon} vs candidate manifest {m_horizon}"))
    return out


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
    # R10-3: the SHARED preconditions are read under the same locks, and their identity is fingerprinted for every class
    with conn.transaction():
        take_locks(conn, chart_id)
        pre = check_preconditions(conn, chart_id=chart_id, generation=generation, classes=classes, ephe_path=ephe_path,
                                  modules=modules, path_refs=path_refs)
        shared_fp = precondition_fingerprint(conn, chart_id, generation)
    report["preconditions"] = pre
    disagreements = []
    for cls in pre["classes"]:
        try:
            with conn.transaction():
                take_locks(conn, chart_id)
                if precondition_fingerprint(conn, chart_id, generation) != shared_fp:
                    raise VerificationRefused(
                        "stale_inputs", "the manifest or the search-input snapshot changed after the preconditions were "
                        "verified — nothing is persisted; re-run")
                report["classes"][cls] = verify_class(
                    conn, chart_id=chart_id, generation=generation, event_class=cls, position_at=position_at,
                    configured_selection=configured_selection_for(cls), path_rulings=path_rulings, h_unknown=h_unknown,
                    moon_scope_domain=moon_scope_domain, factor_rows_for=factor_rows_for, drishti_bound=drishti_bound,
                    vedha_bound=vedha_bound, persist=not report_only, runner=pre.get("runner"))
        except VerificationDisagrees as exc:
            report["classes"][cls] = {"event_class": cls, "status": "DISAGREE", "stage": exc.stage, "detail": exc.detail}
            disagreements.append(cls)
    # R10-4 (iii): the job ends in the SAME combined candidate gate the seal uses (search completeness 1206/1232 + window
    # verification 1240) on the actual candidate manifest. A run over a SUBSET of classes is judged on that subset's
    # violations and the generation-level ones; the rest are reported, never hidden.
    # R11-3: the gate is evaluated in EVERY mode — `--report-only` used to skip it while still naming the combined function as
    # `gate_source`. A report-only run persists nothing, so it can never be VERIFIED; it reports the gate honestly.
    gate_all = candidate_gate_on_candidate_manifest(conn, chart_id, generation)
    scope = set(pre["classes"])
    full = classes is None
    # generation-level violations carry event_class '*' (the completeness function) or None — BOTH are generation-level and
    # always in scope: a subset run must not be able to call a generation-level mismatch "outside its classes" (R11-cand-1)
    gate = [v for v in gate_all if full or v["event_class"] in (None, "*") or v["event_class"] in scope]
    report["gate"] = gate
    report["gate_outside_scope"] = [v for v in gate_all if v not in gate]
    report["gate_source"] = "ka_gochara_candidate_gate_violations"
    verified = [c for c in report["classes"].values() if c.get("status") == "VERIFIED"]
    report["status"] = ("DISAGREE" if disagreements else
                        ("REPORT_ONLY" if report_only else
                         ("VERIFIED" if not gate and len(verified) == len(report["classes"]) else "NOT_VERIFIED")))
    report["cockpit"] = (
        f"REPORT ONLY (nothing persisted) · combined gate: {len(gate)} violation(s)" if report["status"] == "REPORT_ONLY" else
        f"VERIFIED (policy {_policy(report)}, {len(verified)} of {len(report['classes'])} classes, combined gate clean)"
        if report["status"] == "VERIFIED" else
        f"BUILT · NOT VERIFIED · gate CLOSED ({len(gate)} violation(s), {len(disagreements)} disagreement(s))")
    report["exit_code"] = (EXIT_DISAGREE if disagreements or (gate and not report_only) else EXIT_OK)
    return report


def _policy(report) -> str:
    for c in report["classes"].values():
        for w in c.get("windows", ()):
            return w["policy_version"]
    return "n/a"


__all__ += ["VerificationDisagrees", "run", "verify_class"]
