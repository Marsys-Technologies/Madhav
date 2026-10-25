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

import completion                               # TR-26 G-completion predicates (SR-J4E-HORIZON-BASIS): pure functions, no import-time effect
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
#: TR-26 (SR-J4E-CENTURY-FAIL-1 (4)): the 14 scored classes the 12-class trial never ran = input_vector_verifier.SCORED_CLASS_UNIVERSE minus TRIAL_CLASSES_12.  A DATA fact for the
#: 26-class / 14-class gate profiles; a drift test must pin TRIAL_CLASSES_26 equal to that universe (CLAUDE.md §N.7.3 — never a restated constant that can shadow it).
TRIAL_CLASSES_NEW_14 = ("career_advancement", "career_change", "career_entry", "career_setback", "childbirth", "education_milestone", "exam_outcome", "major_gain",
                        "marriage", "relocation", "romantic_start", "separation", "surgery", "travel_event")
TRIAL_CLASSES_26 = TRIAL_CLASSES_12 + TRIAL_CLASSES_NEW_14
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
    checks.append(check(f"the trial ran exactly the {len(want)} required classes", sorted(want) == list(got), list(got), sorted(want)))
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
    checks += g1_baseline_provenance_checks(report, baseline, profile)
    checks += g1_certificate_checks(report, profile)
    return gate("G-1", "Integrity", checks)


def g1_baseline_provenance_checks(report: dict, baseline: dict, profile: dict) -> list[dict]:
    """TR-26 (SR-TR26-PLAN (b): no pre-built baseline — it is made on the VM, first, at the dispatch head, and is a RUN INPUT outside the digest-pinned harness directory): with the profile's
    `baseline_provenance.required` the baseline must say it was built at THE TRIAL'S OWN head and that its own all-null oracle passed.  Absent fields read NOT_EVALUATED, never equal (§N.8)."""
    spec = profile.get("baseline_provenance")
    if not isinstance(spec, dict) or not spec.get("required"):
        return []
    bh, th = _get(baseline, "code", "head"), _get(report, "code", "head")
    passed = _get(baseline, "oracle", "passed")
    return [check("the baseline was built at the trial's own head", None if not bh or not th else bh == th, [bh, th], "equal",
                  note="the baseline is made in the same session at the dispatch head; a baseline of another head does not vouch for this one"),
            check("the baseline's own all-null oracle passed", None if passed is None else passed is True, passed, True)]


def g1_certificate_checks(report: dict, profile: dict) -> list[dict]:
    """TR-26 (cockpit addition to SR-TR26-PLAN; the century failure of SR-J4E-CENTURY-FAIL-1): no earlier gate measured certificate SIZE — the 12 TR #2 classes passed at ~310 cells on headroom
    alone against the 400-cell cap.  With the profile's `certificate_audit.required` the trial report must carry `certificate_audit` (read-only SELECT on the trial DB, trial_slice.cert_audit) for
    every trial class; the check FAILS when any stored certificate exceeds the profile's `max_cells` / `max_bytes` (the database's own caps, migration 1402) — unreachable after the writer fix —
    and REPORTS the headroom per class in `observed`.  A report without the audit is NOT_EVALUATED, never green (§N.8)."""
    spec = profile.get("certificate_audit")
    if not isinstance(spec, dict) or not spec.get("required"):
        return []
    max_cells, max_bytes = spec.get("max_cells"), spec.get("max_bytes")
    audit = report.get("certificate_audit")
    want = sorted(profile.get("trial_classes") or TRIAL_CLASSES_12)
    per = audit.get("classes") if isinstance(audit, dict) else None
    if not isinstance(per, dict) or not isinstance(max_cells, int) or not isinstance(max_bytes, int):
        return [check("every stored solver certificate is inside the database's cell and byte caps", None, "no certificate_audit in the report (or no caps in the profile)",
                      {"max_cells": max_cells, "max_bytes": max_bytes}, note="the audit is a read-only SELECT on the trial database, run before it is dropped")]
    missing = [c for c in want if c not in per]
    over = {c: {"max_cells": v.get("max_cells"), "max_bytes": v.get("max_bytes")} for c, v in sorted(per.items())
            if c in want and ((v.get("max_cells") or 0) > max_cells or (v.get("max_bytes") or 0) > max_bytes)}
    headroom = {c: {"cells": max_cells - (v.get("max_cells") or 0), "bytes": max_bytes - (v.get("max_bytes") or 0), "truncated_windows": v.get("truncated")}
                for c, v in sorted(per.items()) if c in want}
    if missing:
        return [check("every stored solver certificate is inside the database's cell and byte caps", None, f"no audit row for: {missing}", "every trial class")]
    return [check("every stored solver certificate is inside the database's cell and byte caps", not over, over or {"headroom_per_class": headroom},
                  {"max_cells": max_cells, "max_bytes": max_bytes}, note="headroom per class is reported in `observed`; a truncated window is counted, not failed")]


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


def recount_agrees(att: dict, live: dict) -> tuple:
    """R-6 (numerical_window_gate.generation_verdict's own rule): the attested populations are the STORED ones less the verifier's demoted numbered windows.  So the
    attested windows equal the live windows, and the attested numbered equal the live numbered minus the attested demoted set, MATCHED BY window_id: the attested
    `demoted_windows` ([{window_id, reason}], read from the attestation) must list each window once, and each must be a live numbered window (`live.numbered_among_demoted`,
    the listed ids the live table holds with a peak).  A count that is off with no matching demoted id, an id that is not a live numbered window, or an id left unlisted
    FAILS; an attestation that records no demoted set is read as demoting nothing, i.e. the strict equality.  Returns (verdict, observed); verdict None when a side is absent."""
    if not att or not live:
        return None, {"attested": att, "live": live}
    listed = att.get("demoted_windows")
    ids = [e.get("window_id") if isinstance(e, dict) else e for e in (listed if isinstance(listed, list) else [])]
    held = live.get("numbered_among_demoted")
    held = held if isinstance(held, list) else []
    obs = {"attested": {k: v for k, v in att.items() if k != "demoted_windows"}, "live": {k: v for k, v in live.items() if k != "numbered_among_demoted"},
           "demoted": {"listed": len(ids), "distinct": len(set(ids)), "live_numbered": len(set(held) & set(ids)),
                       "not_live_numbered": len(set(ids) - set(held)), "held_but_unlisted": len(set(held) - set(ids))}}
    if att.get("numbered") is None or live.get("numbered") is None:
        return False, obs
    ok = (att.get("windows") == live.get("windows") and len(ids) == len(set(ids)) and all(isinstance(i, str) and i for i in ids) and set(held) == set(ids)
          and att["numbered"] == live["numbered"] - len(ids))
    return ok, obs


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
    ok, observed = recount_agrees(att, live)
    checks.append(check("attestation counts equal the live recount", ok, observed, "attested numbered = live numbered - the attested demoted windows (matched by window_id)"))
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
    return gate("G-4", "Independent verification", checks, source=verification.get("source"), verdict_scope=verification.get("generation_verdict_scope"))


def g4_inconclusive_checks(report: dict, profile: dict) -> list[dict]:
    """TR-26 (SR-KGEW-QUAL-BOUND-AMEND-2 (b), binding): the verifier's INCONCLUSIVE windows (the certificate check could not settle them inside its own budget, so they are demoted to a named
    blank) are counted per class from `verifier_repeat.inconclusive_windows`.  Up to `per_class_accept` (2) in a class and `total_max` (12) in all are ACCEPTED and disclosed window by window in
    `observed` (class, path, window id — ids only) for the seal brief; a 3rd in any class, or more than 12 in total, reads REPORT (REFER-TO-SURROGATE before dispatch), never PASS.
    (I) INTERPRETATION: "honest-null / INCONCLUSIVE count" is the verifier's INCONCLUSIVE verdicts; the builder's own named blanks are counted by G-3's caps.  Profile-gated:
    `verification.inconclusive_thresholds.required`; a report without the record is NOT_EVALUATED."""
    spec = _get(profile, "verification", "inconclusive_thresholds")
    if not isinstance(spec, dict) or not spec.get("required"):
        return []
    claim = f"the verifier's INCONCLUSIVE windows are within {spec.get('per_class_accept')} per class and {spec.get('total_max')} in total"
    wins = _get(report, "verifier_repeat", "inconclusive_windows")
    if not isinstance(wins, list) or not isinstance(spec.get("per_class_accept"), int) or not isinstance(spec.get("total_max"), int):
        return [check(claim, None, "no verifier_repeat.inconclusive_windows in the report (or no thresholds in the profile)", "recorded")]
    per: dict[str, int] = {}
    for w in wins:
        per[w.get("event_class")] = per.get(w.get("event_class"), 0) + 1
    over_class = {c: n for c, n in sorted(per.items()) if n > spec["per_class_accept"]}
    over_total = len(wins) > spec["total_max"]
    disclosed = sorted(({"event_class": w.get("event_class"), "path_id": w.get("path_id"), "window_id": w.get("window_id"), "reason": w.get("reason")} for w in wins),
                       key=lambda d: (str(d["event_class"]), str(d["path_id"]), str(d["window_id"])))
    return [report_check(claim, not over_class and not over_total, {"total": len(wins), "per_class": dict(sorted(per.items())), "classes_over": over_class, "total_over": over_total,
                                                                    "disclosed": disclosed},
                         {"per_class_accept": spec["per_class_accept"], "total_max": spec["total_max"]},
                         note="REFER-TO-SURROGATE before dispatch when exceeded; every accepted window is disclosed in `disclosed` for the seal brief")]


def g5_truncated_resolve_checks(report: dict, profile: dict) -> list[dict]:
    """TR-26 (SR-KGEW-QUAL-BOUND-AMEND-2 (c), binding): the verifier re-solves a window whose stored certificate is `truncated` from scratch, so its wall time is measured and reported
    SEPARATELY (windows, seconds total / max, by class and path) — it feeds the W4 verification re-size.  Not capped here: a measurement, PASS when measured (zero truncated windows is a
    measurement of zero), NOT_EVALUATED when the verifier-repeat record carries none.  Profile-gated: `runtime.truncated_resolve_report`."""
    if not _get(profile, "runtime", "truncated_resolve_report"):
        return []
    tr = _get(report, "verifier_repeat", "truncated_resolve")
    claim = "the verifier's re-solve wall time for the truncated windows is measured and reported separately"
    ok = isinstance(tr, dict) and isinstance(tr.get("windows"), int) and isinstance(tr.get("seconds_total"), (int, float)) and tr.get("windows") == tr.get("windows_timed")
    return [check(claim, True if ok else None, tr if ok else "no truncated-window timing in verifier_repeat (or a truncated window was not timed)", "windows, seconds_total, seconds_max, by_class, by_path")]


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


#: HARNESS-3.2 (D-10) (I) INTERPRETATION: the default load bound (1-minute load average per core) of a profile that does not state one.  A FINAL profile must state it
#: (`runtime.max_load_per_core`); the surrogate's ruling sets the final value.  The shipped profiles carry a named PLACEHOLDER for it.
DEFAULT_MAX_LOAD_PER_CORE = 1.0


def load_validity(report: dict, profile: dict) -> tuple[bool | None, dict, str | None]:
    """Was the writer's runtime measured on a machine quiet enough to mean something?  (True = valid, False = loaded, None = cannot tell; the observed record; why).
    Reads the per-stage `max_load_per_core` of the writer's `build:` stages (the stages the projection sums).  A run that did not record it is unknown, never quiet."""
    rt = profile.get("runtime") or {}
    bound = rt.get("max_load_per_core")
    source = "profile.runtime.max_load_per_core"
    if bound is None:
        if profile.get("final"):
            return None, {"bound": None}, "a final profile states runtime.max_load_per_core"
        bound, source = DEFAULT_MAX_LOAD_PER_CORE, "DEFAULT (I) INTERPRETATION 1.0 — the profile states none"
    stages = _get(report, "effective_wall", "stages", default=None)
    build = {s: v for s, v in sorted(stages.items()) if s.startswith("build:")} if isinstance(stages, dict) else {}
    obs = {"bound_per_core": bound, "bound_source": source, "stages_measured": len(build)}
    if not build:
        return None, obs, "no per-stage load was recorded for the writer's build stages"
    unmeasured = sorted(s for s, v in build.items() if not isinstance(v, dict) or v.get("max_load_per_core") is None)
    over = {s: v["max_load_per_core"] for s, v in build.items() if s not in unmeasured and v["max_load_per_core"] > bound}
    worst = max((v["max_load_per_core"] for s, v in build.items() if s not in unmeasured), default=None)
    obs.update({"max_load_per_core": worst, "stages_over_bound": over, "stages_unmeasured": unmeasured})
    if over:
        return False, obs, f"{len(over)} build stage(s) ran above {bound} load per core"
    if unmeasured:
        return None, obs, f"load was not measured for build stage(s) {unmeasured[:5]}"
    return True, obs, None


def wall_comparability(report: dict) -> tuple[bool, str | None]:
    """AMD64-DOCKER (SR-T24-AMD64-DOCKER, SR-G5-LOAD): is this run's wall time one G-5 may use?  A run that carries a `platform` block with `wall_comparable` false (an emulated
    linux/amd64 container) is not; its seconds are recorded for sizing and nothing else.  A report with no platform block is an ordinary run."""
    plat = report.get("platform")
    if isinstance(plat, dict) and plat.get("wall_comparable") is not True:
        return False, f"the run was executed under emulation ({plat.get('emulation_layer') or 'undetermined'}): its wall time is not comparable and is not used for G-5 (SR-T24-AMD64-DOCKER, SR-G5-LOAD)"
    return True, None


def g5_runtime(report: dict, profile: dict, verification: dict | None) -> dict:
    proj = runtime_projection(report, profile)
    rt = profile.get("runtime") or {}
    checks = []
    n_required = len(profile.get("trial_classes") or TRIAL_CLASSES_12)
    proj["trial_classes_required"] = n_required
    n_trial = proj.get("trial_classes", 0)
    valid, load_obs, load_why = load_validity(report, profile)
    proj["load"] = load_obs
    wall_ok, wall_why = wall_comparability(report)
    claim = "projected century writer time ≤ limit"
    if not wall_ok:
        proj["wall_comparable"] = False
        checks.append(check(claim, None, {"platform": report.get("platform")}, "a wall time measured on the target runtime", note=f"not evaluated: {wall_why}"))
        checks.append(check("verifier solver check ≤ per-class budget (projected to the century horizon)", None, "emulated run", (rt.get("verifier_solver_check_s_per_class", 600)),
                            note=f"not evaluated: {wall_why}"))
        return gate("G-5", "Runtime", checks, projection=proj)
    if n_trial < n_required:
        # D-10: the formula scales the class-less head by n_century/n_trial; with a slice of the trial it multiplies the head by 26 and reads FAIL for the slice, not the build
        checks.append(check(claim, None, {"trial_classes": n_trial, "required": n_required}, f"a trial of {n_required} classes",
                            note="not evaluated: the projection is only meaningful for the full trial it was written for"))
    elif valid is not True:
        checks.append(check(claim, None, load_obs, f"1-minute load average per core ≤ {load_obs.get('bound_per_core')} over every measured build stage",
                            note=f"not evaluated: {load_why}" + ("; re-run on a quiet machine" if valid is False else "")))
    elif proj.get("projected_writer_s") is None or proj.get("limit_s") is None:
        checks.append(check(claim, None, proj, "needs step timings, horizon and class counts"))
    else:
        checks.append(check(claim, proj["projected_writer_s"] <= proj["limit_s"], proj["projected_writer_s"], proj["limit_s"]))
    if rt.get("max_load_per_core") is None and profile.get("final"):
        checks.append(check("the load bound is explicit in a final profile", False, None, "profile.runtime.max_load_per_core"))
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


def g7_determinism(report: dict, second: dict | None, profile: dict | None = None) -> dict:
    """A second trial run produces byte-identical window rows — and, where the profile requires it (TR-26), identical verifier verdicts on every truncated window and the G-6 sample."""
    if not isinstance(second, dict):
        return gate("G-7", "Determinism", [check("a second trial run exists", None, "no second report supplied", "second run")])
    a, b = report.get("window_rows_digest") or {}, second.get("window_rows_digest") or {}
    checks = [check("both runs carry a window-rows digest", bool(a.get("sha256")) and bool(b.get("sha256")), [bool(a.get("sha256")), bool(b.get("sha256"))], [True, True])]
    checks.append(check("both runs are at the same code head", _get(report, "code", "head") == _get(second, "code", "head") and bool(_get(report, "code", "head")),
                        [_get(report, "code", "head"), _get(second, "code", "head")], "equal"))
    checks.append(check("the two runs stored the same number of windows", a.get("windows") == b.get("windows") and a.get("windows") is not None, [a.get("windows"), b.get("windows")], "equal"))
    checks.append(check("the window rows are byte-identical (sha256 over canonical rows)", bool(a.get("sha256")) and a.get("sha256") == b.get("sha256"),
                        [a.get("sha256", "")[:16], b.get("sha256", "")[:16]], "equal"))
    checks += g7_verifier_repeat_checks(report, second, profile or {})
    checks += g7_kill_resume_checks(report, second, profile or {})
    return gate("G-7", "Determinism", checks)


GENERIC_REFUSALS = ("Exception", "BaseException", "RuntimeError", "AssertionError", "KeyError", "AttributeError", "TypeError", "ValueError", "OSError", "SystemExit")


def g7_kill_resume_checks(report: dict, second: dict, profile: dict) -> list[dict]:
    """TR-26 (SR-RESUME-NOW, binding): the SECOND run is the KILL+RESUME leg — the century build deterministically aborted after substep N (a committed class behind, a window-sweep substep next), then resumed.
    With the profile's `determinism.kill_resume.required`, G-7 PASSES only if (1) the resumed run says where it was killed, with >= 1 class committed and the next substep inside the window sweep; (2) the
    skipped substeps provably did not re-run — the harness's own producer-execution log (not the writer's ledger) shows no substep executed both before the kill and after the resume, and before ∪ after is
    exactly the plan; (3) the resumed generation is BYTE-IDENTICAL to the fresh one over EVERY trial class (the window-rows digest, its per-class digests and the membership digest; a class missing from either
    side is NOT_EVALUATED, so the leg can only stand in for a plain second run when it covers all of them); (4) a resume attempted with a different program digest REFUSED BY NAME before running any substep
    (a generic exception name, or a message that does not mention the digest, is not a refusal by name).  Every missing record is NOT_EVALUATED, never a pass (§N.8)."""
    spec = _get(profile, "determinism", "kill_resume")
    if not isinstance(spec, dict) or not spec.get("required"):
        return []
    rl = second.get("resume_leg")
    if not isinstance(rl, dict) or not isinstance(rl.get("killed_after_substep"), int) or not rl.get("resumed"):
        return [check("the second run is a kill+resume leg that was resumed", None, "no resume_leg in the second report" if not isinstance(rl, dict) else {"resumed": rl.get("resumed")}, "killed and resumed")]
    plan, before, after = rl.get("plan_substeps") or [], rl.get("executed_before_abort") or [], rl.get("executed_after_resume") or []
    checks = [check("the kill landed inside the window sweep with at least one class already committed",
                    bool(rl.get("classes_committed_at_abort")) and str(rl.get("abort_next_step") or "").split(":")[0] == "window" and rl["killed_after_substep"] >= 1,
                    {"killed_after_substep": rl["killed_after_substep"], "committed_classes": len(rl.get("classes_committed_at_abort") or []), "next_step_kind": str(rl.get("abort_next_step") or "").split(":")[0]},
                    ">=1 committed class, next substep kind window")]
    rerun = sorted(set(before) & set(after))
    complete = bool(plan) and sorted(set(before) | set(after)) == sorted(set(plan)) and len(before) == rl["killed_after_substep"] and bool(after)
    checks.append(check("the substeps skipped on resume did not re-run, and before-kill plus after-resume is exactly the plan", None if not plan or not before else (not rerun and complete),
                        {"ran_before_kill": len(before), "ran_after_resume": len(after), "plan": len(plan), "rerun": len(rerun), "rerun_examples": rerun[:3]}, "no substep in both; union == plan"))
    want = sorted(profile.get("trial_classes") or TRIAL_CLASSES_12)
    da, db = report.get("window_rows_digest") or {}, second.get("window_rows_digest") or {}
    pa, pb = da.get("per_class") or {}, db.get("per_class") or {}
    if sorted(pa) != want or sorted(pb) != want:
        checks.append(check("the fresh and the resumed generation are compared over every trial class", None, {"fresh_missing": sorted(set(want) - set(pa)), "resumed_missing": sorted(set(want) - set(pb))}, f"all {len(want)} classes"))
    else:
        diff = sorted(c for c in want if pa[c] != pb[c])
        same = bool(da.get("sha256")) and da.get("sha256") == db.get("sha256") and bool(da.get("memberships_sha256")) and da.get("memberships_sha256") == db.get("memberships_sha256") and not diff
        checks.append(check("the resumed generation is byte-identical to the fresh one over every trial class (rows, per-class rows, memberships)", same,
                            {"classes": len(want), "differing_classes": diff, "rows_equal": da.get("sha256") == db.get("sha256"), "memberships_equal": da.get("memberships_sha256") == db.get("memberships_sha256")}, "equal"))
    pr = rl.get("refusal_probe")
    needle = str(spec.get("refusal_message_contains") or "digest").lower()
    if not isinstance(pr, dict) or not pr.get("attempted"):
        checks.append(check("a resume with a different program digest refuses by name", None, "no refusal probe recorded", "refused by name"))
    else:
        ok, obs = refused_by_name(pr, needle)
        checks.append(check("a resume with a different program digest refuses by name", ok, obs, "refused before any substep, by a named refusal that mentions the digest"))
    for dim in spec.get("refusal_dimensions") or []:             # SR-RESUME-NOW (3): the source digest and the library digest are perturbed ONE AT A TIME; each must refuse by name on its own
        rec = (pr.get("by_dimension") or {}).get(dim) if isinstance(pr, dict) else None
        claim = f"a resume with a different {dim} digest refuses by name"
        if not isinstance(rec, dict) or not rec.get("attempted"):
            checks.append(check(claim, None, f"no {dim}-digest refusal probe recorded", "refused by name"))
        else:
            ok, obs = refused_by_name(rec, needle)
            checks.append(check(claim, ok, obs, "refused before any substep, by a named refusal that mentions the digest"))
    return checks


def refused_by_name(pr: dict, needle: str) -> tuple:
    """(True | False, observed) for one refusal-probe record: the resume was refused, before any substep ran, by an exception that is not a generic one and whose message mentions the digest."""
    name, msg = pr.get("refusal_name"), str(pr.get("message") or "")
    named = bool(name) and name not in GENERIC_REFUSALS and needle in msg.lower()
    ok = bool(pr.get("refused")) and pr.get("executed_substeps") == 0 and named
    return ok, {"refused": pr.get("refused"), "refusal_name": name, "message_mentions_digest": needle in msg.lower(), "substeps_run": pr.get("executed_substeps")}


def _demoted(report: dict) -> list | None:
    d = _get(report, "verification", "attestation_recount", "attested", "demoted_windows")
    if not isinstance(d, list):
        return None
    return sorted((str(x.get("window_id")), str(x.get("reason"))) for x in d if isinstance(x, dict))


def g7_verifier_repeat_checks(report: dict, second: dict, profile: dict) -> list[dict]:
    """TR-26 (SR-TR26-PLAN (a), binding cockpit finding): W4's two verification passes do NOT compare per-window verdicts (its dry run is judged on `report.gate == []` and capacity only, and a
    report-only run persists nothing), so G-7 compares them itself.  With the profile's `determinism.verifier_repeat.required`, BOTH runs must carry `verifier_repeat` (trial_slice.verifier_repeat_section:
    the solver-check verdict of every window the verifier's certificate check reached, the ids of the windows whose certificate is `truncated`, the ids of run 1's G-6 cross-check sample) and
    G-7 PASSES only if, for every audited window (truncated windows ∪ the G-6 sample), the verdict of run 2 equals run 1's, the truncated sets are equal, and the demoted (INCONCLUSIVE) windows the
    attestations name are the same.  A missing record, an uncovered class, an unmapped verdict or a truncated window the solver check never reached is NOT_EVALUATED, never a pass (§N.8)."""
    spec = _get(profile, "determinism", "verifier_repeat")
    if not isinstance(spec, dict) or not spec.get("required"):
        return []
    claim = "the verifier's per-window verdicts on the truncated windows and the G-6 sample are identical in both runs"
    ra, rb = report.get("verifier_repeat"), second.get("verifier_repeat")
    if not (isinstance(ra, dict) and isinstance(rb, dict) and isinstance(ra.get("verdicts"), dict) and isinstance(rb.get("verdicts"), dict)):
        return [check(claim, None, {"run1": isinstance(ra, dict), "run2": isinstance(rb, dict)}, "both runs carry verifier_repeat",
                      note="run 2 must verify (TR_G7_VERIFY=1), not be build-only: the repeat is the verifier's own verdicts")]
    want = sorted(profile.get("trial_classes") or TRIAL_CLASSES_12)
    covered = [sorted(r.get("classes_covered") or []) for r in (ra, rb)]
    unmapped = [r.get("unmapped_verdicts") for r in (ra, rb)]
    gaps = {"classes_not_covered": [sorted(set(want) - set(c)) for c in covered], "unmapped_verdicts": unmapped}
    if any(c != want for c in covered) or any(u != 0 for u in unmapped):
        return [check("the verifier-repeat record covers every trial class and maps every verdict to a window", None, gaps, "every class, 0 unmapped")]
    ta, tb = sorted(ra.get("truncated_window_ids") or []), sorted(rb.get("truncated_window_ids") or [])
    g6 = ra.get("g6_sample_window_ids")
    if not isinstance(g6, list):
        return [check("run 1 recorded its G-6 sample", None, "absent", "present", note="run 1 must run the cross-check (its sample is the G-6 sample)")]
    checks = [check("the truncated windows (solver_certificate.truncated = true) are the same windows in both runs", ta == tb, {"run1": len(ta), "run2": len(tb)}, "equal")]
    va, vb = ra["verdicts"], rb["verdicts"]
    never = sorted(w for w in set(ta) | set(tb) if w not in va or w not in vb)
    checks.append(check("every truncated window reached the verifier's solver check in both runs", None if never else True,
                        {"truncated": len(ta), "without_verdict": [w[:8] for w in never[:5]], "count": len(never)}, "all", note="a truncated window with no verdict is a detector that did not run" if never else None))
    audit = sorted(set(ta) | set(tb) | set(g6))
    differ = sorted(w for w in audit if va.get(w) != vb.get(w))
    g6_with_verdict = sum(1 for w in set(g6) if w in va and w in vb)          # sample windows the solver check reached in BOTH runs (the rest compare absent-in-both, i.e. vacuously)
    state = False if differ else (True if g6_with_verdict else None)          # a difference is a FAIL whatever the sample; an equal comparison over NO sample verdict is no evidence (§N.8)
    checks.append(check(claim, state, {"audited": len(audit), "truncated": len(ta), "g6_sample": len(g6), "g6_with_verdict": g6_with_verdict,
                                       "differing": len(differ), "examples": [{"window": w[:8], "run1": va.get(w), "run2": vb.get(w)} for w in differ[:5]]}, "0 differing, >= 1 G-6 sample window with a verdict in both runs",
                        note="a window with no solver verdict (verified by exact re-derivation) is compared as absent-in-both; a sample with none is NOT_EVALUATED" if not g6_with_verdict else
                        "a window with no solver verdict (verified by exact re-derivation) is compared as absent-in-both"))
    da, db = _demoted(report), _demoted(second)
    if da is None or db is None:
        checks.append(check("the windows the attestations demote (INCONCLUSIVE) are the same in both runs", None, {"run1": da is not None, "run2": db is not None}, "both recorded"))
    else:
        checks.append(check("the windows the attestations demote (INCONCLUSIVE) are the same in both runs", da == db, {"run1": len(da), "run2": len(db)}, "equal"))
    sa, sb = ({c: (v or {}).get("status") for c, v in (_get(r, "verification", "classes", default={}) or {}).items()} for r in (report, second))
    checks.append(check("every trial class has the same verification status in both runs", None if not sa or not sb else sa == sb, {"run1": len(sa), "run2": len(sb)}, "equal"))
    return checks


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
        if not (isinstance(d, dict) and sorted(d) == ["from", "path", "ruling", "to"] and d["path"] in PATH_IDS and isinstance(d["from"], str) and isinstance(d["to"], str)):
            raise DecisionTableError(f"declared rule-version change {d!r} is not {{path, from, to, ruling}}")
        rl = d["ruling"]       # an identity move is declared WITH the ruling(s) it stands on (B.3): a move with no ruling is a finding, never a declaration
        if not (isinstance(rl, list) and rl and all(isinstance(x, str) and x for x in rl) and len(set(rl)) == len(rl)):
            raise DecisionTableError(f"declared rule-version change {d['path']} {d['from']} -> {d['to']} names no ruling (a non-empty list of ruling ids is required)")
    body = {k: v for k, v in table.items() if k != "sha256"}
    return {**body, "sha256": sha256_of(body)}


def _table_profile(table: dict, profile: dict) -> dict:
    """The profile as G-2 reads it under a decision table: the table's forbidden list is the zero list and its allowed list the closed set (no owner-answer rules)."""
    return {**profile, "zero_reasons": list(table["forbidden_reasons"]), "allowed_reasons": [{"reason": r, "when": {}} for r in table["allowed_reasons"]]}


def _reason_census(report: dict) -> tuple[dict, dict]:
    """(windows carrying each code in either place, primary blank reason counts) — the two places a code can hide."""
    return dict(report.get("reason_windows_any") or {}), dict(_get(report, "totals", "blank_reasons", default={}) or {})


#: SR-NEAR-STATION-TIE (option A): the trial STOPS when more than 0.5 % of ANY class's windows are blanked by the near-station tie rule (per mille, integer arithmetic).
NEAR_STATION_TIE_CAP_PER_MILLE = 5
NEAR_STATION_TIE_REFUSAL = "near_station_tie_cap_exceeded"


def near_station_tie_check(report: dict) -> dict:
    """SR-NEAR-STATION-TIE: the report's `near_station_tie` section (`window_sweep.near_station_tie_report`, lane od1-plateau-tie) carries the per-class count of windows
    blanked by the near-station tie rule; a class above 0.5 % of its windows is the named refusal `near_station_tie_cap_exceeded`.  The section is null where the checkout has no such
    function (it exists only on the od1 integration line): the check then reads NOT_EVALUATED — never a pass for a count nobody took (§N.8).  The cap is the harness's own constant,
    judged per class from the section's `per_class` counts; the function's own aggregate `cap_exceeded` is read only as a second stop."""
    claim = f"near-station tie blanks at most {NEAR_STATION_TIE_CAP_PER_MILLE / 10:.1f} % of every class's windows ({NEAR_STATION_TIE_REFUSAL}; SR-NEAR-STATION-TIE)"
    sec = report.get("near_station_tie")
    per = sec.get("per_class") if isinstance(sec, dict) else None
    if not isinstance(per, dict) or not per or sec.get("near_station_tie_blanked") is None:
        return check(claim, None, report.get("near_station_tie_unavailable") or "the report carries no near-station tie count", "per-class counts from window_sweep.near_station_tie_report",
                     note="not evaluated: the count could not be taken (the function is absent from this checkout)")
    counts = {c: {"windows": v.get("windows"), "blanked": v.get("blanked")} for c, v in sorted(per.items()) if isinstance(v, dict)}
    if len(counts) != len(per) or any(not isinstance(v["windows"], int) or not isinstance(v["blanked"], int) for v in counts.values()):
        return check(claim, None, per, "an integer windows and blanked per class", note="not evaluated: the per-class counts are malformed")
    over = {c: v for c, v in counts.items() if v["windows"] and v["blanked"] * 1000 > v["windows"] * NEAR_STATION_TIE_CAP_PER_MILLE}
    stop = bool(over) or sec.get("cap_exceeded") is True
    if stop:
        return check(claim, False, {"refusal": NEAR_STATION_TIE_REFUSAL, "classes_over_cap": over, "per_class": counts, "near_station_tie_blanked": sec["near_station_tie_blanked"]},
                     NEAR_STATION_TIE_CAP_PER_MILLE / 1000, note=f"REFUSE: {NEAR_STATION_TIE_REFUSAL}")
    if not any(v["windows"] for v in counts.values()):
        return check(claim, None, counts, "windows>0")
    return check(claim, True, {"near_station_tie_blanked": sec["near_station_tie_blanked"], "per_class": counts}, NEAR_STATION_TIE_CAP_PER_MILLE / 1000)


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
    checks.append(near_station_tie_check(report))
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

def g8_completion_checks(report: dict, profile: dict) -> list[dict]:
    """TR-26 G-completion (SR-J4E-HORIZON-BASIS, SR-J4E-POSTRUN-READBACKS): the two century completion-gate checks the trial itself never exercised, re-run on the probe's RAW readbacks by the pack's
    own predicates (`completion.horizon_basis_check`, `completion.provenance_check`) — the probe's words are never the verdict.  With the profile's `completion.required`:
    (1) `horizon_basis`: a century-shaped (unmarked, staged-century-config) manifest carries a non-null `horizon_basis` pin, candidate status, the TRIAL's own ruled horizon;
    (2) `digests_equal_dry_run` receipts: a build that went through the REAL build entry (`asset_runner.run_asset`) wrote a provenance receipt whose code_digest equals the expected_code_digest and whose
        build_id is that run.  A missing record is NOT_EVALUATED; a completed run with no receipt (a bypass of the real entry, TR #2's shape) and an unpinned manifest read FALSE."""
    spec = _get(profile, "completion")
    if not isinstance(spec, dict) or not spec.get("required"):
        return []
    hz = report.get("horizon")
    ruled = [hz.get("start"), hz.get("end")] if isinstance(hz, dict) and isinstance(hz.get("start"), str) and isinstance(hz.get("end"), str) else None
    sec = report.get("completion")
    got = completion.evaluate_record(sec, ruled)
    hb, pv = got["horizon_basis"], got["provenance"]
    return [check("a century-shaped manifest (unmarked run, staged century config) carries a pinned horizon_basis", hb[0], hb[1], "candidate manifest, ruled horizon, horizon_basis pinned",
                  note=None if hb[0] is not None else "not evaluated: " + hb[1]),
            check("a build through the real build entry (asset_runner.run_asset) wrote a provenance receipt with the expected code digest and this run's build id", pv[0], pv[1],
                  "non-empty receipts; code_digest == expected_code_digest; build_id == run id", note=None if pv[0] is not None else "not evaluated: " + pv[1])]


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
    # D-10 (review 3879 B-1): the same two guards as g5_runtime — the projection is only meaningful for the full trial, measured on a quiet machine
    claim = "projected effective wall (compute + lock wait) ≤ limit"
    n_required = len(profile.get("trial_classes") or TRIAL_CLASSES_12)
    valid, load_obs, load_why = load_validity(report, profile)
    wall_ok, wall_why = wall_comparability(report)
    if not wall_ok:                                                            # AMD64-DOCKER: an emulated run's wall time is not used
        checks.append(check(claim, None, {"platform": report.get("platform")}, "a wall time measured on the target runtime", note=f"not evaluated: {wall_why}"))
        return checks
    if n_trial < n_required:
        checks.append(check(claim, None, {"trial_classes": n_trial, "required": n_required}, f"a trial of {n_required} classes",
                            note="not evaluated: the projection is only meaningful for the full trial it was written for"))
        return checks
    if valid is not True:
        checks.append(check(claim, None, load_obs, f"1-minute load average per core ≤ {load_obs.get('bound_per_core')} over every measured build stage",
                            note=f"not evaluated: {load_why}" + ("; re-run on a quiet machine" if valid is False else "")))
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
    g5, g7, g8 = g5_runtime(report, profile, verification), g7_determinism(report, second_report, profile), g8_head_identity(report, dispatch_modules)
    if a10:
        for g, extra in ((g5, g5_effective_wall_checks(report, profile)), (g7, g7_noninterference_checks(report, baseline, decision_table)),
                         (g8, g8_digest_checks(report, dispatch_digests))):
            g["checks"] = g["checks"] + extra
            g["status"] = roll_up(g["checks"])
    g8["checks"] = g8["checks"] + g8_completion_checks(report, profile)                              # TR-26 G-completion (profile-gated; a profile without `completion` adds nothing)
    g8["status"] = roll_up(g8["checks"])
    g5 = g5_cpu.apply_to_gate(g5, report, profile, check=check, roll_up=roll_up, runtime_projection=runtime_projection)         # G5-CPU hook: wall | attributed_cpu | neither
    g4 = g4_verification(report, verification)
    for g, extra in ((g4, g4_inconclusive_checks(report, profile)), (g5, g5_truncated_resolve_checks(report, profile))):
        if extra:
            g["checks"] = g["checks"] + extra
            g["status"] = roll_up(g["checks"])
    gates = [g1_integrity(report, baseline, profile), g2, g3, g4, g5, g6_crosscheck(report, crosscheck, profile), g7, g8]
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
