"""Dispatch-gate evaluator G-1 .. G-8 (PLAN.md §4.3), the century projection (G-5) and the report helpers.  Job-local; not repository code.

PURE: no database, no checkout import, no clock.  Input = the trial report(s) the driver writes, the 12-class all-null baseline, and a GATE PROFILE (data).
Every doctrine-dependent number (the owner's answers, the closed set of legitimate blank reasons, the share floors) is read from the profile; this module
holds none.  A profile with `"final": false` can never produce a dispatchable verdict, however green the gates read.

Honesty rules (root CLAUDE.md §N.7/§N.8): a gate is PASS only when a detector measured its claim and the claim held; FAIL when the measurement says no;
NOT_EVALUATED when the input the detector needs is absent or vacuous (zero numbered windows, no second run, no verification, ...).  NOT_EVALUATED is never
green and never a pass.  Output is counts, class ids, reason codes, seconds and hashes only.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import g5_cpu                                   # G5-CPU (SR-G5-LOAD): the attributed-CPU method of G-5; pure helpers, no import-time effect

PASS, FAIL, NOT_EVALUATED = "PASS", "FAIL", "NOT_EVALUATED"
#: a KNOWN shortfall the G-3 decision table sends to the surrogate for a dispatch ruling (PLAN v2 §5): not a pass, not a refusal.  Outranked by FAIL and by NOT_EVALUATED.
REPORT = "REPORT"
GATE_IDS = ("G-1", "G-2", "G-3", "G-4", "G-5", "G-6", "G-7", "G-8")
#: the 25 TRIAL_READY/1 checks (PLAN_A10_1 §2.2); the merged evaluator's own REQUIRED_IDS is cross-checked against this in the tests
TRIAL_READY_PREDICATE = "TRIAL_READY/1"
TRIAL_READY_IDS = tuple("T%02d" % n for n in range(1, 26))
TRIAL_CLASSES_12 = ("bereavement", "chronic_onset", "illness_acute", "major_loss", "achievement_recognition", "business_launch", "financial_deception",
                    "foreign_settlement", "parental_event", "property_acquisition", "psychological_arc", "spiritual_turn")
#: the anomaly fields of `trial_report.json` that must all be zero (G-1); a missing field is a detector that did not run, not a zero
ANOMALY_FIELDS = ("number_without_score", "peak_without_score", "valence_without_score", "blank_without_reason_code")
SOLVER_BUDGET_REASON = "solver_budget_exhausted"
ATTESTATION_BLOCKING_FLAG = "no_window_numbered_under_numerical_policy"


# ── building blocks ─────────────────────────────────────────────────────────────────────────────────────────────

def check(claim: str, ok: bool | None, observed: Any = None, expected: Any = None, note: str | None = None) -> dict:
    """One claim, one detector.  ok True → PASS, False → FAIL, None → NOT_EVALUATED (the detector had no input)."""
    out = {"claim": claim, "status": NOT_EVALUATED if ok is None else (PASS if ok else FAIL), "observed": observed, "expected": expected}
    if note:
        out["note"] = note
    return out


def report_check(claim: str, ok: bool | None, observed: Any = None, expected: Any = None, note: str | None = None) -> dict:
    """Like `check`, but a False reads REPORT (a shortfall the decision table sends to the surrogate), not FAIL."""
    out = check(claim, ok, observed, expected, note)
    if out["status"] == FAIL:
        out["status"] = REPORT
    return out


def roll_up(checks: list[dict]) -> str:
    if not checks:
        return NOT_EVALUATED
    statuses = {c["status"] for c in checks}
    if FAIL in statuses:
        return FAIL
    if NOT_EVALUATED in statuses:
        return NOT_EVALUATED
    if REPORT in statuses:
        return REPORT
    return PASS


def gate(gid: str, name: str, checks: list[dict], **extra) -> dict:
    return {"id": gid, "name": name, "status": roll_up(checks), "checks": checks, **extra}


def _get(d: Any, *path, default=None):
    for p in path:
        if not isinstance(d, dict) or p not in d:
            return default
        d = d[p]
    return d


def share(num: int | None, den: int | None) -> float | None:
    return None if not den or num is None else num / den


# ── profile (data) ──────────────────────────────────────────────────────────────────────────────────────────────

def answers_of(profile: dict) -> dict:
    return dict(profile.get("answers") or {})


def allowed_reasons(profile: dict) -> tuple[set, list]:
    """The CLOSED set of blank reasons the owner's answers leave legitimate: each rule is {reason, when: {question: [answers]}} and holds iff every
    listed question's answer is in its list (an empty/absent `when` holds always).  A rule naming a question the profile has no answer for does NOT hold,
    and is returned in the second value so the verdict says which rule could not be decided."""
    answers, allowed, undecided = answers_of(profile), set(), []
    for rule in profile.get("allowed_reasons") or []:
        when = rule.get("when") or {}
        if all(q in answers and answers[q] in opts for q, opts in when.items()):
            allowed.add(rule["reason"])
        elif any(q not in answers for q in when):
            undecided.append(rule["reason"])
    return allowed, undecided


def floor_for(profile: dict, key: str) -> tuple[float | None, str | None]:
    """A share floor from the profile: a number, or {by: <question>, floors: {answer: number}} resolved through the owner's answer.  (None, why) when it
    cannot be resolved — the gate then reads NOT_EVALUATED, never a default floor."""
    spec = _get(profile, "share_floors", key)
    if isinstance(spec, (int, float)):
        return float(spec), None
    if isinstance(spec, dict) and "by" in spec:
        ans = answers_of(profile).get(spec["by"])
        if ans in (spec.get("floors") or {}):
            return float(spec["floors"][ans]), None
        return None, f"no floor for {key}: answer {spec['by']}={ans!r} not in {sorted(spec.get('floors') or {})}"
    return None, f"profile carries no share floor {key!r}"


# ── G-1 .. G-8 ──────────────────────────────────────────────────────────────────────────────────────────────────

def g1_integrity(report: dict, baseline: dict, profile: dict) -> dict:
    """windows_total per class equals the all-null baseline; anomalies 0."""
    checks = []
    want = tuple(profile.get("trial_classes") or TRIAL_CLASSES_12)
    got = tuple(sorted(_get(report, "config", "classes", default=[])))
    checks.append(check("the trial ran exactly the 12 required classes", sorted(want) == list(got), list(got), sorted(want)))
    base_classes = baseline.get("classes") or {}
    unmeasured = sorted(c for c in want if _get(base_classes, c, "windows_total") is None)
    checks.append(check("the baseline carries a measured window count for every required class", None if unmeasured else True, unmeasured or "all measured", "all measured",
                        note="an unmeasured baseline class makes G-1 unevaluable, never a pass" if unmeasured else None))
    diffs = {}
    for c in want:
        b, r = _get(base_classes, c, "windows_total"), _get(report, "classes", c, "windows_total")
        if b is not None and r != b:
            diffs[c] = {"baseline": b, "trial": r}
    if unmeasured and not diffs:
        checks.append(check("windows_total per class equals the all-null baseline", None, "baseline unmeasured for " + ",".join(unmeasured), "equal"))
    else:
        checks.append(check("windows_total per class equals the all-null baseline", not diffs, diffs or "equal for every measured class", "equal"))
    an = report.get("anomalies") or {}
    missing = [k for k in ANOMALY_FIELDS if k not in an]
    nonzero = {k: an[k] for k in an if k in ANOMALY_FIELDS or k.startswith("peaks_without") if an[k]}
    if missing:
        checks.append(check("anomalies are all zero", None, f"anomaly detector(s) absent: {missing}", 0))
    else:
        checks.append(check("anomalies are all zero", not nonzero, nonzero or 0, 0))
    return gate("G-1", "Integrity", checks)


def census_gap(report: dict) -> str | None:
    """Why the reason census cannot support a "no forbidden reason" / "inside the closed set" / "cap not breached" reading, or None when it can (§N.8).  Those readings are
    absences ("nothing in the census"), so they are only measurements when the census is PRESENT and ACCOUNTS FOR EVERY BLANK WINDOW: `totals.blank_reasons` sums to
    `totals.blank` and `reason_windows_any` exists.  With no blank window there is nothing to account for, but `totals.blank` itself must have been counted."""
    blank = _get(report, "totals", "blank")
    if not isinstance(blank, int) or isinstance(blank, bool):
        return "totals.blank absent: the blank windows were not counted"
    if blank == 0:
        return None
    primary, any_ = _get(report, "totals", "blank_reasons"), report.get("reason_windows_any")
    if not isinstance(primary, dict) or not isinstance(any_, dict) or not any_:
        return f"{blank} blank window(s) but the reason census is absent or empty"
    counts = list(primary.values())
    if not all(isinstance(n, int) and not isinstance(n, bool) for n in counts):
        return "totals.blank_reasons holds a non-integer count"
    if sum(counts) != blank:
        return f"the census accounts for {sum(counts)} of {blank} blank windows"
    return None


def g2_wiring(report: dict, profile: dict) -> dict:
    """Zero blanks under the five wiring codes; every other blank reason inside the closed set the owner's answers allow."""
    checks = []
    total = _get(report, "totals", "windows_total", default=0)
    zero = list(profile.get("zero_reasons") or [])
    any_ = report.get("reason_windows_any") or {}
    if not total:
        return gate("G-2", "Wiring complete", [check("the trial stored windows", None, total, ">0")])
    if not zero:
        checks.append(check("the profile names the wiring codes that must be zero", None, [], "five codes"))
    gap = census_gap(report)       # a census that does not account for every blank window measures nothing: a reason's absence is then unknown, never a pass
    for code in zero:
        seen = any_.get(code, 0)
        checks.append(check(f"no window is blank under {code} (as primary or any secondary reason)", False if seen else (None if gap else True), seen or gap or 0, 0))
    allowed, undecided = allowed_reasons(profile)
    primary = _get(report, "totals", "blank_reasons", default={}) or {}
    secondary = _get(report, "totals", "unresolved_factors_in_blank_windows", default={}) or {}
    outside_p = {r: n for r, n in primary.items() if r not in allowed and r not in zero}
    outside_s = {r: v.get("windows") if isinstance(v, dict) else v for r, v in secondary.items() if r not in allowed and r not in zero}
    checks.append(check("every primary blank reason is inside the closed allowed set", False if outside_p else (None if gap else True), outside_p or gap or "inside the set",
                        sorted(allowed), note=f"rules undecided for want of an owner answer: {undecided}" if undecided else None))
    checks.append(check("every secondary (any-member) unresolved reason in a blank window is inside the closed allowed set", False if outside_s else (None if gap else True),
                        outside_s or gap or "inside the set", sorted(allowed)))
    return gate("G-2", "Wiring complete", checks, allowed_reasons=sorted(allowed), undecided_rules=undecided)


def path_shares(report: dict) -> dict:
    out = {}
    for p, v in (report.get("paths") or {}).items():
        out[p] = {"windows": v.get("windows"), "numbered": v.get("numbered"), "share": share(v.get("numbered"), v.get("windows"))}
    return out


def g3_shares(report: dict, profile: dict) -> dict:
    """P3 ∪ P4 numbered ≥ floor; P2, P1 ≥ the floor for the chosen answers; solver_budget_exhausted ≤ cap of all windows."""
    paths = report.get("paths") or {}
    checks = []

    def pooled(ids):
        w = sum(paths.get(p, {}).get("windows") or 0 for p in ids)
        n = sum(paths.get(p, {}).get("numbered") or 0 for p in ids)
        return w, n

    for label, ids, key in (("P3 ∪ P4", ("P3", "P4"), "p3_p4"), ("P2", ("P2",), "p2"), ("P1", ("P1",), "p1")):
        floor, why = floor_for(profile, key)
        w, n = pooled(ids)
        if floor is None or not w:
            checks.append(check(f"{label} numbered share ≥ floor", None, {"windows": w, "numbered": n}, why or "windows>0"))
        else:
            checks.append(check(f"{label} numbered share ≥ floor", n / w >= floor, {"windows": w, "numbered": n, "share": round(n / w, 4)}, floor))
    total = _get(report, "totals", "windows_total", default=0)
    cap = _get(profile, "solver_budget_exhausted_max_share")
    n_budget = (report.get("reason_windows_any") or {}).get(SOLVER_BUDGET_REASON, 0)
    gap = census_gap(report)
    if not total or cap is None or (gap and n_budget / total <= cap):      # a breach already visible is a FAIL whatever else is missing; an unproven "under" is not a pass
        checks.append(check(f"{SOLVER_BUDGET_REASON} ≤ cap of all windows", None, gap or n_budget, cap))
    else:
        checks.append(check(f"{SOLVER_BUDGET_REASON} ≤ cap of all windows", n_budget / total <= cap, {"windows": n_budget, "of": total, "share": round(n_budget / total, 5)}, cap))
    return gate("G-3", "Share floors", checks, shares=path_shares(report))


def g4_verification(report: dict, verification: dict | None) -> dict:
    """The independent verification job re-derived every window: verdict PASSED, numbered > 0, no blocking flag, attested counts = live recount, none UNVERIFIED."""
    if not isinstance(verification, dict) or not verification.get("ran"):
        why = (verification or {}).get("not_run_reason", "no verification record supplied") if isinstance(verification, dict) else "no verification record supplied"
        return gate("G-4", "Independent verification", [check("the verification job ran against this trial", None, why, "ran")])
    v = verification.get("generation_verdict") or {}
    st = v.get("status")      # the gate module's own vocabulary: PASSED / FAILED / NOT_APPLICABLE; anything but PASSED is not a pass
    checks = [check("numerical_window_gate.generation_verdict is PASSED", None if not st else st == "PASSED", st, "PASSED",
                    note="; ".join((v.get("problems") or [])[:3]) or None if st and st != "PASSED" else None)]
    nb = v.get("numbered_windows")
    checks.append(check("numbered_windows > 0", None if nb is None else nb > 0, nb, ">0"))
    flags = v.get("judgment_flags")
    checks.append(check(f"no {ATTESTATION_BLOCKING_FLAG} flag", None if flags is None else ATTESTATION_BLOCKING_FLAG not in flags, flags, f"not {ATTESTATION_BLOCKING_FLAG}"))
    rec = verification.get("attestation_recount") or {}
    att, live = rec.get("attested") or {}, rec.get("live") or {}
    ok = None if not att or not live else (att.get("windows") == live.get("windows") and att.get("numbered") == live.get("numbered"))
    checks.append(check("attestation counts equal the live recount", ok, {"attested": att, "live": live}, "equal"))
    # the live recount must itself be the trial's own count (a recount of another database would be vacuous)
    tot, wp = _get(report, "totals", "windows_total"), _get(report, "totals", "with_peak")
    if live:
        checks.append(check("the live recount is the trial's own window count", live.get("windows") == tot and live.get("numbered") == wp,
                            {"live": live, "trial": {"windows": tot, "numbered": wp}}, "equal"))
    un = verification.get("unverified_windows")
    cls = verification.get("classes") or {}
    not_verified = {c: s.get("status") for c, s in cls.items() if s.get("status") != "VERIFIED"}
    checks.append(check("UNVERIFIED windows = 0", None if un is None else un == 0, un, 0))
    checks.append(check("every class VERIFIED", None if not cls else not not_verified, not_verified or "all VERIFIED", "VERIFIED"))
    return gate("G-4", "Independent verification", checks, source=verification.get("source"))


def runtime_projection(report: dict, profile: dict) -> dict:
    """Century projection of the writer (and the verifier's solver check).  GATING number = the plan's formula: (base_s + solver_s) · (26/12) · r
    (× the profile's local→cloud speed factor, default 1).  base_s = every substep but the window phase; solver_s = the window phase (the solver runs in the
    writer's `window:` substeps).  The class-less head (rules, convention, bodies, manifest, snapshot) does not grow with the class count, so the REFINED figure
    scales only the class-scoped seconds by 26/12 — reported, informational (the plan's figure is the conservative one)."""
    rt = profile.get("runtime") or {}
    kinds = _get(report, "runtime_s", "by_step_kind", default={}) or {}
    head_kinds = set(_get(report, "runtime_s", "head_kinds", default=["rules", "convention", "body", "manifest", "snapshot"]))
    n_trial = len(_get(report, "config", "classes", default=[]) or [])
    n_cent = rt.get("century_classes", 26)
    days_trial = _get(report, "horizon", "days")
    horizon = rt.get("century_horizon")
    if horizon:
        from datetime import datetime
        days_cent = (datetime.fromisoformat(horizon[1]) - datetime.fromisoformat(horizon[0])).total_seconds() / 86400.0
        r_source = "profile.runtime.century_horizon"
    else:
        days_cent, r_source = days_trial, "ASSUMED equal to the trial horizon (profile.runtime.century_horizon is null)"
    r = (days_cent / days_trial) if days_trial and days_cent else None
    speed = float(rt.get("speed_factor", 1.0))
    solver_s = float(kinds.get("window", 0.0))
    base_s = float(sum(v for k, v in kinds.items() if k != "window"))
    out = {"base_s": round(base_s, 2), "solver_s": round(solver_s, 2), "trial_classes": n_trial, "century_classes": n_cent, "r": None if r is None else round(r, 6),
           "r_source": r_source, "speed_factor": speed}
    if not n_trial or r is None or not kinds:
        out["projected_writer_s"] = None
        return out
    scale = n_cent / n_trial
    out["projected_writer_s"] = round((base_s + solver_s) * scale * r * speed, 1)
    head_s = sum(v for k, v in kinds.items() if k in head_kinds)
    class_s = sum(v for k, v in kinds.items() if k not in head_kinds)
    out["projected_writer_s_refined"] = round((head_s + class_s * scale) * r * speed, 1)
    cap, frac, margin = rt.get("cap_s", 72000), rt.get("abort_fraction", 0.8), rt.get("margin", 0.75)
    out["limit_s"] = round(cap * frac * margin, 1)
    out["limit_derivation"] = f"{cap} × {frac} × {margin}"
    return out


def g5_runtime(report: dict, profile: dict, verification: dict | None) -> dict:
    proj = runtime_projection(report, profile)
    rt = profile.get("runtime") or {}
    checks = []
    if proj.get("projected_writer_s") is None or proj.get("limit_s") is None:
        checks.append(check("projected century writer time ≤ limit", None, proj, "needs step timings, horizon and class counts"))
    else:
        checks.append(check("projected century writer time ≤ limit", proj["projected_writer_s"] <= proj["limit_s"], proj["projected_writer_s"], proj["limit_s"]))
    if rt.get("century_horizon") is None and profile.get("final"):
        checks.append(check("the century horizon is explicit in a final profile", False, None, "profile.runtime.century_horizon"))
    per_class_cap = rt.get("verifier_solver_check_s_per_class", 600)
    vclasses = (verification or {}).get("classes") or {}
    secs = {c: s.get("window_check_s") for c, s in vclasses.items() if s.get("window_check_s") is not None}
    r = proj.get("r") or 1.0
    if not secs:
        checks.append(check("verifier solver check ≤ per-class budget (projected to the century horizon)", None, "no per-class verifier timing", per_class_cap))
    else:
        worst = max(secs.items(), key=lambda kv: kv[1])
        projected = worst[1] * r
        checks.append(check("verifier solver check ≤ per-class budget (projected to the century horizon)", projected <= per_class_cap,
                            {"worst_class": worst[0], "measured_s": round(worst[1], 2), "projected_s": round(projected, 2)}, per_class_cap))
    return gate("G-5", "Runtime", checks, projection=proj)


def g6_crosscheck(report: dict, crosscheck: dict | None, profile: dict) -> dict:
    """The cross-check sample re-solved by dense brute force (windows ≤ 3 days) / the legacy sampler (elsewhere)."""
    if not isinstance(crosscheck, dict):
        return gate("G-6", "Cross-check", [check("the cross-check ran against this trial", None, "no cross-check record supplied", "ran")])
    cc = profile.get("crosscheck") or {}
    rate = cc.get("sample_rate", 0.03)
    n_num = _get(report, "totals", "with_peak", default=0)
    checks = [check("the cross-check ran to completion", crosscheck.get("status") == "COMPLETE", crosscheck.get("status"), "COMPLETE", note=crosscheck.get("detail"))]
    if crosscheck.get("status") != "COMPLETE":
        return gate("G-6", "Cross-check", checks)
    if not n_num:
        checks.append(check("there are numbered windows to cross-check", None, n_num, ">0"))
        return gate("G-6", "Cross-check", checks)
    checks.append(check("the sample was drawn from this trial's numbered windows", crosscheck.get("numbered_windows") == n_num, crosscheck.get("numbered_windows"), n_num))
    need = math.ceil(rate * n_num)
    checks.append(check(f"random sample ≥ {rate:.0%} of numbered windows", (crosscheck.get("sampled") or 0) >= need, crosscheck.get("sampled"), need))
    req, got = crosscheck.get("top_mixed_requested"), crosscheck.get("top_mixed_checked")
    checks.append(check("every window with a mixed piece in the top-N was checked", None if req is None or got is None else got == req, {"requested": req, "checked": got}, "all"))
    sv = crosscheck.get("sampler_violations") or []
    checks.append(check("solver value ≥ legacy sampler value on every window", not sv, len(sv), 0, note=str(sv[:3]) if sv else None))
    dv = crosscheck.get("dense_violations") or []
    dn = _get(crosscheck, "dense", "windows", default=0)
    checks.append(check("brute force (1 s) equals the stored value on the dense subset", not dv, {"violations": len(dv), "dense_windows": dn}, 0, note=str(dv[:3]) if dv else None))
    ri = crosscheck.get("recompute_inconsistent") or []
    checks.append(check("the recomputed objective at the stored peak equals the stored value", not ri, len(ri), 0, note=str(ri[:3]) if ri else None))
    return gate("G-6", "Cross-check", checks, sample={k: crosscheck.get(k) for k in ("seed", "sampled", "numbered_windows", "top_mixed_requested", "top_mixed_checked")})


def g7_determinism(report: dict, second: dict | None) -> dict:
    """A second trial run produces byte-identical window rows."""
    if not isinstance(second, dict):
        return gate("G-7", "Determinism", [check("a second trial run exists", None, "no second report supplied", "second run")])
    a, b = report.get("window_rows_digest") or {}, second.get("window_rows_digest") or {}
    checks = [check("both runs carry a window-rows digest", bool(a.get("sha256")) and bool(b.get("sha256")), [bool(a.get("sha256")), bool(b.get("sha256"))], [True, True])]
    checks.append(check("both runs are at the same code head", _get(report, "code", "head") == _get(second, "code", "head") and bool(_get(report, "code", "head")),
                        [_get(report, "code", "head"), _get(second, "code", "head")], "equal"))
    checks.append(check("the two runs stored the same number of windows", a.get("windows") == b.get("windows") and a.get("windows") is not None, [a.get("windows"), b.get("windows")], "equal"))
    checks.append(check("the window rows are byte-identical (sha256 over canonical rows)", bool(a.get("sha256")) and a.get("sha256") == b.get("sha256"),
                        [a.get("sha256", "")[:16], b.get("sha256", "")[:16]], "equal"))
    return gate("G-7", "Determinism", checks)


def g8_head_identity(report: dict, dispatch_modules: dict | None) -> dict:
    """Every IMPLEMENTATION_MODULES file at the trial head equals the dispatch head."""
    trial = _get(report, "code", "implementation_modules")
    if not isinstance(trial, dict) or not trial:
        return gate("G-8", "Head identity", [check("the trial recorded its implementation-module digests", None, "absent", "present")])
    if not isinstance(dispatch_modules, dict) or not dispatch_modules:
        return gate("G-8", "Head identity", [check("the dispatch head's implementation-module digests were supplied", None, "absent", "present")])
    only_t, only_d = sorted(set(trial) - set(dispatch_modules)), sorted(set(dispatch_modules) - set(trial))
    differ = sorted(m for m in set(trial) & set(dispatch_modules) if trial[m] != dispatch_modules[m])
    checks = [check("the same set of implementation modules", not only_t and not only_d, {"only_trial": only_t, "only_dispatch": only_d}, "equal sets"),
              check("every module file digest is equal", not differ, differ or f"{len(trial)} equal", "equal")]
    return gate("G-8", "Head identity", checks)


# ── A10.1 additions: the G-3 decision table, noninterference, the digests record, effective wall, TRIAL_READY (G-0) ─────────────────────────────────
# Active when `evaluate` is given a `decision_table` (the trial driver ALWAYS gives one; a library caller that omits it gets the pre-A10.1 evaluator).

TABLE_SCHEMA = "ky.g3_decision_table/1"
TABLE_KEYS = ("schema", "table_id", "source", "rows", "caps", "allowed_reasons", "forbidden_reasons", "noninterference")
NONINTERFERENCE_KINDS = ("windows", "supports", "contacts", "membership")
PATH_IDS = ("P1", "P2", "P3", "P4")
DIGEST_COMPONENTS = ("registry", "l0", "ephemeris", "convention", "orb_policy", "rulings", "config")


class DecisionTableError(ValueError):
    """The G-3 decision table is not a usable table: the run is refused (a gate without its table would be a silent default)."""


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_of(obj: Any) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def load_decision_table(table: Any) -> dict:
    """Validate the table (data) and return it with its own `sha256` (over the canonical table without that key).  Raises DecisionTableError."""
    if not isinstance(table, dict) or table.get("schema") != TABLE_SCHEMA:
        raise DecisionTableError(f"schema is not {TABLE_SCHEMA}")
    extra = sorted(k for k in table if k not in TABLE_KEYS and k != "sha256")
    missing = sorted(k for k in TABLE_KEYS if k not in table)
    if extra or missing:
        raise DecisionTableError(f"table keys: missing {missing}, unknown {extra}")

    def reasons(key: str) -> list:
        v = table[key]
        if not isinstance(v, list) or not v or not all(isinstance(x, str) and x for x in v) or len(set(v)) != len(v):
            raise DecisionTableError(f"{key} must be a non-empty list of distinct reason names")
        return v
    allowed, forbidden = set(reasons("allowed_reasons")), set(reasons("forbidden_reasons"))
    if allowed & forbidden:
        raise DecisionTableError(f"a reason is both allowed and forbidden: {sorted(allowed & forbidden)}")
    ids = set()
    for row in table["rows"] if isinstance(table["rows"], list) else []:
        ok = (isinstance(row, dict) and isinstance(row.get("id"), str) and row["id"] not in ids and isinstance(row.get("floor"), (int, float))
              and 0 < row["floor"] <= 1 and row.get("shortfall") == "REPORT" and row.get("forbidden") == "REFUSE"
              and isinstance(row.get("paths"), list) and row["paths"] and all(p in PATH_IDS or p == "*" for p in row["paths"]))
        if not ok:
            raise DecisionTableError(f"row {row!r} is not {{id, paths, floor in (0,1], shortfall REPORT, forbidden REFUSE}}")
        ids.add(row["id"])
    if not ids:
        raise DecisionTableError("the table has no floor rows")
    cap_ids = set()
    for cap in table["caps"] if isinstance(table["caps"], list) else []:
        ok = (isinstance(cap, dict) and isinstance(cap.get("id"), str) and cap["id"] not in cap_ids and isinstance(cap.get("max_share"), (int, float))
              and 0 <= cap["max_share"] < 1 and cap.get("of") == "all_windows" and cap.get("above") == "REFUSE"
              and isinstance(cap.get("reasons"), list) and cap["reasons"] and set(cap["reasons"]) <= allowed)
        if not ok:
            raise DecisionTableError(f"cap {cap!r} is not {{id, reasons (allowed ones), max_share in [0,1), of all_windows, above REFUSE}}")
        cap_ids.add(cap["id"])
    if not cap_ids:
        raise DecisionTableError("the table has no caps")
    ni = table["noninterference"]
    if not isinstance(ni, dict) or tuple(ni.get("kinds") or ()) != NONINTERFERENCE_KINDS:
        raise DecisionTableError(f"noninterference.kinds must be exactly {list(NONINTERFERENCE_KINDS)}")
    for d in ni.get("declared_rule_version_changes") or []:
        if not (isinstance(d, dict) and sorted(d) == ["from", "path", "to"] and d["path"] in PATH_IDS and isinstance(d["from"], str) and isinstance(d["to"], str)):
            raise DecisionTableError(f"declared rule-version change {d!r} is not {{path, from, to}}")
    body = {k: v for k, v in table.items() if k != "sha256"}
    return {**body, "sha256": sha256_of(body)}


def _table_profile(table: dict, profile: dict) -> dict:
    """The profile as G-2 reads it under a decision table: the table's forbidden list is the zero list and its allowed list the closed set (no owner-answer rules)."""
    return {**profile, "zero_reasons": list(table["forbidden_reasons"]), "allowed_reasons": [{"reason": r, "when": {}} for r in table["allowed_reasons"]]}


def _reason_census(report: dict) -> tuple[dict, dict]:
    """(windows carrying each code in either place, primary blank reason counts) — the two places a code can hide."""
    return dict(report.get("reason_windows_any") or {}), dict(_get(report, "totals", "blank_reasons", default={}) or {})


def g3_decision_table(report: dict, table: dict) -> dict:
    """PLAN v2 §5 as data: (1) no forbidden reason anywhere (REFUSE); (2) no reason outside the closed allowed set (REFUSE); (3) each floor row: PASS at or above
    the floor, REPORT (to the surrogate) below it when every blank reason of the row is allowed, FAIL when the row carries a forbidden/unknown reason; (4) each
    cap: FAIL above it.  A row or cap with nothing to measure reads NOT_EVALUATED."""
    allowed, forbidden = set(table["allowed_reasons"]), set(table["forbidden_reasons"])
    any_, primary = _reason_census(report)
    paths = report.get("paths") or {}
    total = _get(report, "totals", "windows_total", default=0) or 0
    present = {r: n for r, n in any_.items() if n} | {r: n for r, n in primary.items() if n}
    for pv in paths.values():                       # a reason visible in ANY census of the report counts, wherever the report keeps it
        for key in ("blank_by_reason", "windows_with_reason"):
            for r, n in (pv.get(key) or {}).items():
                if n:
                    present.setdefault(r, n)
    bad_forbidden = {r: any_.get(r, 0) or primary.get(r, 0) for r in sorted(present) if r in forbidden}
    unknown = {r: n for r, n in sorted(present.items()) if r not in allowed and r not in forbidden}
    gap = census_gap(report)       # a census that does not account for every blank window measures nothing: a reason's absence is then unknown, never a pass
    checks = [check("no forbidden reason on any window (primary or secondary): zero required", False if bad_forbidden else (None if (not total or gap) else True),
                    bad_forbidden or gap or 0, 0, note="a forbidden reason is a REFUSAL, whatever the shares read"),
              check("no blank reason outside the closed allowed set", False if unknown else (None if (not total or gap) else True), unknown or gap or "inside the set", sorted(allowed))]
    for row in table["rows"]:
        ids = sorted(paths) if row["paths"] == ["*"] else row["paths"]
        w = sum(paths.get(p, {}).get("windows") or 0 for p in ids)
        n = sum(paths.get(p, {}).get("numbered") or 0 for p in ids)
        per_path = [paths[p] for p in ids if p in paths and (paths[p].get("blank_by_reason") is not None or paths[p].get("windows_with_reason") is not None)]
        if per_path:      # the row's own reasons
            row_reasons = {r for pv in per_path for r in list((pv.get("blank_by_reason") or {}) | (pv.get("windows_with_reason") or {}))}
            basis = "reasons of the row's paths"
        else:             # the report carries no per-path reasons: the whole run's census (stricter: a reason anywhere spoils the shortfall)
            row_reasons, basis = set(present), "reasons of the whole run (no per-path reason census)"
        outside = sorted(r for r in row_reasons if r not in allowed)
        label = f"{row['id']} numbered share ≥ {row['floor']:.0%}"
        if not w:
            checks.append(check(label, None, {"windows": w, "numbered": n}, "windows>0"))
            continue
        obs = {"windows": w, "numbered": n, "share": round(n / w, 4)}
        if n / w >= row["floor"]:
            checks.append(check(label, True, obs, row["floor"]))
        elif outside:
            checks.append(check(label, False, obs, row["floor"], note=f"shortfall WITH reason(s) outside the allowed set {outside} ({basis}): REFUSE"))
        elif gap and not per_path:      # no per-path reasons and no complete whole-run census: whether every blank reason is allowed is unknown
            checks.append(check(label, None, obs, row["floor"], note=f"shortfall below the floor and its reasons are unknown: {gap}"))
        else:
            checks.append(report_check(label, False, obs, row["floor"], note=f"shortfall, every blank reason allowed ({basis}): REPORT to the surrogate for a dispatch ruling"))
    for cap in table["caps"]:
        n = sum(any_.get(r, 0) for r in cap["reasons"])
        label = f"{cap['id']} ≤ {cap['max_share']:.1%} of all windows"
        if not total or (gap and n / total <= cap["max_share"]):
            checks.append(check(label, None, gap or n, cap["max_share"]))
        else:
            checks.append(check(label, n / total <= cap["max_share"], {"windows": n, "of": total, "share": round(n / total, 5)}, cap["max_share"],
                                note="REFUSE above the cap"))
    return gate("G-3", "Share floors and caps (decision table)", checks, shares=path_shares(report), table={"id": table["table_id"], "sha256": table.get("sha256")})


def g0_trial_ready(report: dict) -> dict:
    """G-0: the report embeds a TRIAL_READY/1 evaluation for THIS trial's code head, and every required check reads true — recomputed here from the embedded
    checks, never read off the evaluator's own `ready` flag alone (§N.8).  An evaluation that did not run is NOT_EVALUATED; a check that read false is FAIL; a null one
    (evidence unreadable) is NOT_EVALUATED — the evaluator's own rule that null counts as not ready, kept distinguishable."""
    tr = report.get("trial_ready")
    if not isinstance(tr, dict) or tr.get("not_run_reason"):
        return gate("G-0", "TRIAL_READY/1", [check("TRIAL_READY/1 was evaluated for this trial", None,
                                                    (tr or {}).get("not_run_reason", "no trial_ready section in the report"), "evaluated")])
    cks = tr.get("checks") if isinstance(tr.get("checks"), list) else []
    by_id: dict = {}
    for c in cks:
        if isinstance(c, dict):
            by_id.setdefault(c.get("id"), []).append(c.get("value"))
    false_ids = sorted(i for i in TRIAL_READY_IDS if False in by_id.get(i, []))
    null_ids = sorted(i for i in TRIAL_READY_IDS if i not in false_ids and by_id.get(i) != [True])
    head = _get(report, "code", "head")
    return gate("G-0", "TRIAL_READY/1", [
        check("the predicate is TRIAL_READY/1", tr.get("predicate") == TRIAL_READY_PREDICATE, tr.get("predicate"), TRIAL_READY_PREDICATE),
        check("TRIAL_READY/1 was evaluated at this trial's code head", bool(head) and tr.get("head_sha") == head, [tr.get("head_sha"), head], "equal"),
        check("every required check T01..T25 is present once and true", False if false_ids else (None if null_ids else True),
              {"false": false_ids, "null_or_missing": null_ids} if (false_ids or null_ids) else "all true", "all true", note="a null is not ready (§N.7.6)"),
        check("the evaluator's own ready flag is true", tr.get("ready") is True, tr.get("ready"), True)])


# ── noninterference (GPT N3; PLAN v2 G-7) ────────────────────────────────────────────────────────────────────

def g7_noninterference_checks(report: dict, baseline: dict, table: dict) -> list[dict]:
    """At the same geometry configuration the sorted natural keys of windows, supports, contacts and membership equal the all-null baseline's; only a DECLARED
    rule-version identity change may differ.  Counts alone are not enough: a moved boundary, a substituted contact or a changed membership keeps every count."""
    snap, base = report.get("noninterference"), (baseline or {}).get("noninterference")
    if not isinstance(base, dict) or not isinstance(snap, dict):
        return [check("natural-key snapshots exist for the trial and the baseline", None,
                      {"trial": isinstance(snap, dict), "baseline": isinstance(base, dict)}, "both",
                      note="a baseline made before A10.1 carries no snapshot: re-make it (`make_baseline.sh`); equal counts do not prove noninterference")]
    if not snap.get("geometry_config") or snap.get("geometry_config") != base.get("geometry_config"):
        return [check("the baseline was made at the trial's geometry configuration", None, {"trial": snap.get("geometry_config"), "baseline": base.get("geometry_config")},
                      "equal", note="an unknown configuration, or two different ones, may legitimately give different keys: re-make the baseline at this configuration")]
    checks = [check("the baseline was made at the trial's geometry configuration", True, snap.get("geometry_config"), "equal")]
    for kind in table["noninterference"]["kinds"]:
        a, b = _get(snap, "kinds", kind), _get(base, "kinds", kind)
        if not isinstance(a, dict) or not isinstance(b, dict):
            checks.append(check(f"{kind}: natural keys equal the baseline", None, {"trial": isinstance(a, dict), "baseline": isinstance(b, dict)}, "both captured"))
            continue
        ga, gb = a.get("groups") or {}, b.get("groups") or {}
        differ = sorted(g for g in set(ga) | set(gb) if ga.get(g) != gb.get(g))
        # None == None is not equality (§N.8): both sides must carry a string sha256 and an integer count, else nothing was compared
        typed = all(isinstance(x.get("sha256"), str) and x["sha256"] and isinstance(x.get("count"), int) and not isinstance(x.get("count"), bool) for x in (a, b))
        if not typed:
            checks.append(check(f"{kind}: natural keys equal the baseline", None, {"trial": [a.get("sha256") is not None, a.get("count")], "baseline": [b.get("sha256") is not None, b.get("count")]},
                                "sha256 and count on both sides", note="a snapshot without its digest or count compares nothing"))
            continue
        checks.append(check(f"{kind}: natural keys equal the baseline", not differ and a["sha256"] == b["sha256"] and a["count"] == b["count"],
                            {"count": [a.get("count"), b.get("count")], "differing_groups": differ[:12]}, "equal", note="groups are class|path; names only"))
    # the rule-version identities: baseline versions, with the DECLARED changes applied, must be the trial's versions
    declared = {(d["path"], d["from"]): d["to"] for d in table["noninterference"].get("declared_rule_version_changes") or []}
    tv, bv = snap.get("rule_versions") or {}, base.get("rule_versions") or {}
    expected = {p: sorted({declared.get((p, v), v) for v in vs}) for p, vs in bv.items()}
    got = {p: sorted(vs) for p, vs in tv.items()}
    undeclared = {p: {"baseline": bv.get(p), "trial": got.get(p), "expected_after_declared_changes": expected.get(p)} for p in sorted(set(expected) | set(got)) if expected.get(p) != got.get(p)}
    checks.append(check("rule-version identities differ from the baseline only by declared changes", not undeclared, undeclared or "equal after declared changes", "equal"))
    return checks


# ── the digests record (PLAN v2 G-8: a later L0 / registry / ephemeris / config change invalidates the trial) ────────────────────────────

def g8_digest_checks(report: dict, dispatch_digests: dict | None) -> list[dict]:
    rec = report.get("digests_record")
    comps = rec.get("components") if isinstance(rec, dict) else None
    if not isinstance(comps, dict) or not comps:
        return [check("the trial recorded its registry/L0/ephemeris/convention/orb/rulings/config digests", None, "absent", "present")]
    absent = [c for c in DIGEST_COMPONENTS if not (isinstance(comps.get(c), dict) and comps[c].get("sha256"))]
    if absent:
        return [check("the trial recorded every digest component", None, f"absent: {absent}", list(DIGEST_COMPONENTS))]
    dcomps = dispatch_digests.get("components") if isinstance(dispatch_digests, dict) else None
    if not isinstance(dcomps, dict) or not dcomps:
        return [check("the dispatch head's digests record was supplied", None, "absent", "present")]
    differ = sorted(c for c in DIGEST_COMPONENTS if (dcomps.get(c) or {}).get("sha256") != comps[c]["sha256"])
    return [check("registry, L0, ephemeris, convention, orb policy, rulings and config digests equal at dispatch", not differ, differ or "equal", "equal")]


# ── G-5 effective wall (T17): compute and lock wait, separately ─────────────────────────────────────────────────

WALL_SLACK_S = 0.05


def g5_effective_wall_checks(report: dict, profile: dict) -> list[dict]:
    """The writer's wall is compute + lock wait, measured separately per stage.  Compute alone under the limit with the lock wait over it is a FAIL: the cap is on the
    EFFECTIVE wall."""
    ew = report.get("effective_wall")
    stages = ew.get("stages") if isinstance(ew, dict) else None
    if not isinstance(stages, dict) or not stages:
        return [check("per-stage compute and lock wait are reported separately", None, "no effective_wall section", "present")]
    unmeasured = sorted(s for s, v in stages.items() if not isinstance(v, dict) or v.get("lock_wait_s") is None or v.get("compute_s") is None or v.get("wall_s") is None)
    if unmeasured:
        return [check("per-stage compute and lock wait are reported separately", None, f"lock wait not measured for {unmeasured}", "measured",
                      note="a stage whose lock wait could not be sampled is unknown, never zero")]
    broken = {s: {k: v[k] for k in ("wall_s", "compute_s", "lock_wait_s")} for s, v in sorted(stages.items())
              if abs(v["compute_s"] + v["lock_wait_s"] - v["wall_s"]) > WALL_SLACK_S or v["lock_wait_s"] < 0 or v["compute_s"] < 0}
    checks = [check("per stage, compute + lock wait = wall (and neither is negative)", not broken, broken or "consistent", "wall = compute + lock wait")]
    proj = runtime_projection(report, profile)
    n_trial, n_cent, r, speed = proj.get("trial_classes"), proj.get("century_classes"), proj.get("r"), proj.get("speed_factor", 1.0)
    limit = proj.get("limit_s")
    writer = {s: v for s, v in stages.items() if s.startswith("build:")}
    if not n_trial or r is None or limit is None or not writer:
        checks.append(check("projected effective wall (compute + lock wait) ≤ limit", None, proj, "needs writer stages, horizon and class counts"))
        return checks
    scale = n_cent / n_trial * r * speed
    compute, lock = sum(v["compute_s"] for v in writer.values()) * scale, sum(v["lock_wait_s"] for v in writer.values()) * scale
    checks.append(check("projected effective wall (compute + lock wait) ≤ limit", compute + lock <= limit,
                        {"projected_compute_s": round(compute, 1), "projected_lock_wait_s": round(lock, 1), "effective_s": round(compute + lock, 1)}, limit,
                        note="the cap is on the effective wall; compute alone is reported beside it"))
    return checks


# ── trial validity (not a gate: a trial that did not run as designed is INVALID, whatever the gates say) ─────────

def trial_validity(report: dict) -> dict:
    b = report.get("build") or {}
    checks = [check("the build completed with no defect and no abort", not b.get("defects") and not b.get("aborted") and not b.get("dead_classes"),
                    {"defects": len(b.get("defects") or []), "aborted": b.get("aborted"), "dead_classes": b.get("dead_classes")}, "none"),
              check("the requested numerical policy took effect (manifest and every window)", _get(report, "policy_effect", "took_effect") is True,
                    _get(report, "policy_effect", "took_effect"), True)]
    return {"status": roll_up(checks), "checks": checks}


# ── the verdict ─────────────────────────────────────────────────────────────────────────────────────────────────

def evaluate(report: dict, baseline: dict, profile: dict, *, second_report: dict | None = None, dispatch_modules: dict | None = None,
             verification: dict | None = None, crosscheck: dict | None = None, decision_table: dict | None = None,
             dispatch_digests: dict | None = None) -> dict:
    """The dispatch-gate verdict.  `verification` / `crosscheck` default to the sections embedded in `report`.

    With a `decision_table` (validated by `load_decision_table`; the trial driver ALWAYS passes one) the evaluator is the A10.1 one: G-0 TRIAL_READY/1; G-2 reads the
    table's forbidden list and closed allowed set; G-3 is the decision table (floors → REPORT/REFUSE, caps); G-5 adds the effective wall (compute and lock wait
    separately); G-7 adds the natural-key noninterference comparison; G-8 adds the digests record.  Without one it is the pre-A10.1 evaluator (profile floors)."""
    verification = verification if verification is not None else report.get("verification")
    crosscheck = crosscheck if crosscheck is not None else report.get("crosscheck")
    a10 = decision_table is not None
    g2 = g2_wiring(report, _table_profile(decision_table, profile) if a10 else profile)
    g3 = g3_decision_table(report, decision_table) if a10 else g3_shares(report, profile)
    g5, g7, g8 = g5_runtime(report, profile, verification), g7_determinism(report, second_report), g8_head_identity(report, dispatch_modules)
    if a10:
        for g, extra in ((g5, g5_effective_wall_checks(report, profile)), (g7, g7_noninterference_checks(report, baseline, decision_table)),
                         (g8, g8_digest_checks(report, dispatch_digests))):
            g["checks"] = g["checks"] + extra
            g["status"] = roll_up(g["checks"])
    g5 = g5_cpu.apply_to_gate(g5, report, profile, check=check, roll_up=roll_up, runtime_projection=runtime_projection)         # G5-CPU hook: wall | attributed_cpu | neither
    gates = [g1_integrity(report, baseline, profile), g2, g3, g4_verification(report, verification), g5, g6_crosscheck(report, crosscheck, profile), g7, g8]
    if a10:
        gates.insert(0, g0_trial_ready(report))
    by = {g["id"]: g["status"] for g in gates}
    validity = trial_validity(report)
    failed = [g for g, s in by.items() if s == FAIL]
    unevaluated = [g for g, s in by.items() if s == NOT_EVALUATED]
    reported = [g for g, s in by.items() if s == REPORT]
    final = bool(profile.get("final"))
    if validity["status"] != PASS:
        overall = "INVALID_TRIAL"
    elif failed:
        overall = "NO_DISPATCH"
    elif unevaluated:
        overall = "NO_DISPATCH_NOT_EVALUATED"
    elif reported:
        overall = "NO_DISPATCH_REPORT_TO_SURROGATE"
    elif not final:
        overall = "ALL_GATES_PASS_PROFILE_NOT_FINAL"
    else:
        overall = "DISPATCH_GATE_MET"
    out = {"schema": "ky.trial_gate_verdict/1", "marker": "TRIAL_SLICE", "overall": overall, "dispatchable": overall == "DISPATCH_GATE_MET",
           "failed": failed, "not_evaluated": unevaluated, "reported": reported,
           "profile": {"id": profile.get("profile_id"), "final": final, "answers": answers_of(profile), "provenance": profile.get("provenance")},
           "trial_validity": validity, "gates": {g["id"]: g for g in gates},
           "note": "A profile that is not final (owner confirmation pending) cannot yield DISPATCH_GATE_MET; NOT_EVALUATED is never a pass; REPORT is a known shortfall for the surrogate."}
    if a10:
        out["decision_table"] = {"id": decision_table["table_id"], "sha256": decision_table.get("sha256")}
    return out


# ── the real verification job's JSON report → the shape G-4 / G-5 read ──────────────────────────────────────────

def verification_from_job_report(job: dict, recount: dict | None = None) -> dict:
    """Normalise the stdout JSON of `pipeline.orchestrator.verification_job` (`ky` report: `classes`, `numerical_window_gate`, `gate`).  The job report carries no
    independent recount and no timings, so unless `recount` ({attested, live}) is supplied the attestation claim of G-4 — and the verifier half of G-5 — read
    NOT_EVALUATED, never green.  `unverified_windows` counts the windows of every grain whose status is not VERIFIED; a class with no status is unknown (None)."""
    classes, unverified, unknown = {}, 0, False
    for c, entry in (job.get("classes") or {}).items():
        st = (entry or {}).get("status")
        classes[c] = {"status": st, "window_check_s": None}
        if st is None:
            unknown = True
        for w in (entry or {}).get("windows") or []:
            if w.get("status") != "VERIFIED":
                unverified += int(w.get("windows") or 0)
        if st != "VERIFIED" and not (entry or {}).get("windows"):
            unknown = True
    return {"ran": bool(job.get("classes")), "source": "verification_job_report", "not_run_reason": None if job.get("classes") else "the report carries no classes",
            "generation_verdict": job.get("numerical_window_gate") or {}, "attestation_recount": recount,
            "unverified_windows": None if unknown and not unverified else unverified, "classes": classes}
