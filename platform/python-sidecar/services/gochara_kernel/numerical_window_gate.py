"""The NUMERICAL-WINDOW GATE (OD-1, SR-OD1-DESIGN; root CLAUDE.md §N.8) — the seal's own detector for `window_qualification/1`.

Under the all-NULL policy a window carries no number, so the migration-1240 gate and `window_verifier` have nothing numerical to be wrong about. Under
`window_qualification/1` every window carries (or honestly lacks) a strength (score / evidence), a peak and a valence, and "the 1240 row says VERIFIED" is not by itself
a claim about those numbers. This gate is that claim, measured:

  * the VERIFICATION JOB (verifier principal) re-derives strength, peak and valence of EVERY window from the stored members and the bound factor rows
    (`window_verifier.verify_window_semantics`, which imports nothing from the builder) through the frozen qualification table the manifest binds, and — per grain —
    recounts the stored windows with its own SQL: a window is NUMBERED (a peak is stored) or BLANK (no peak, an explicit reason code, the unqualified valence). The
    two counts must agree with the re-derivation (`grain_attestation`; any mismatch raises). A PASSED attestation per grain is persisted in the grain's 1240 row (the
    runner-identity object the verifier principal writes: no migration is needed for it) — it is therefore inside the seal brief's attestations and digest;
  * `generation_verdict` reads those attestations back and the LIVE stored windows, and is PASSED only when every included grain carries a PASSED attestation naming the
    table the manifest binds, whose counts equal what is stored now. The seal brief carries the verdict; the sealing job refuses to seal `window_qualification/1`
    unless it is PASSED (`require_passed`); the approval-time brief check and the approval summary read it.

Windows the policy cannot number (a time-varying factor, an unmapped categorical factor, an undeclared kernel applicability…) are HONEST NULLS: they carry an explicit
reason code, are counted by reason in the verdict and the brief, and are NEVER a refusal by themselves. What is a refusal: a blank without a reason, a number where the
table yields none, a blank where it yields a value, a reason that names the all-NULL policy under this one (a stub), a table other than the frozen one.

POPULATIONS AFTER CLASSIFICATION (R-6). The verifier's solver check gives every function-valued window one of three classes: AGREED, DISAGREEMENT (blocks the
seal, always: `verify_window_semantics` raises) or INCONCLUSIVE (it could not settle the window inside its own budget, or R-1/R-3's tie refusals). An INCONCLUSIVE
window that carries a number is DEMOTED: the attestation counts it as a BLANK under its named reason, not as numbered, and lists it under `demoted` (the stored row
still carries the builder's number; what is attested and sealed is that the window is served as the named blank). The attestation therefore NAMES them
(`demoted_windows`: sorted `{window_id, reason}`): `generation_verdict` checks that each is a stored numbered window of the grain and that the list agrees with the counts,
and `serving_reader` reads the list back and serves each listed window with every number null and `unqualified_reason` the attested reason. The census the gate recounts is the STORED
populations; the attested populations are the stored ones after classification, and every difference is a named, counted demotion. The demoted share of all windows
is capped at 0.5 % (`INCONCLUSIVE_SHARE_CAP`); above it the verdict FAILS and the seal refuses. A stored blank the check could not confirm stays the blank it is.

This module keeps its OWN literals (the frozen table's binding comes from the vector verifier's, not the builder's `result_policy`; a test asserts they are equal)."""
from __future__ import annotations

import json
from typing import Any

SCHEMA = "numerical_window_gate/1"
PASSED, FAILED, NOT_APPLICABLE = "PASSED", "FAILED", "NOT_APPLICABLE"
POLICY_QUALIFICATION = "window_qualification/1"
POLICY_ALL_NULL = "all_null_candidate/1"
ATTESTATION_KEY = "numerical_window_gate"                 # the key inside the 1240 row's runner_identity

#: the reason codes the policy leaves a window blank under, grouped for the disclosure (the group is a label; the CODE is what is counted and stored). A code in no group
#: is still counted, under `other_named_reason`: a blank is never nameless.
TIME_VARYING = "time_varying_factor"
CATEGORICAL = "categorical_factor_unmapped"
APPLICABILITY = "kernel_applicability_undeclared"
OTHER = "other_named_reason"
REASON_GROUPS = {
    "dynamic_objective_solver_guarantee_not_available": TIME_VARYING,
    "state_boundaries_incomplete": TIME_VARYING,
    "graduated_drishti_source_not_landed": TIME_VARYING,
    "vedha_overlay_not_bound": TIME_VARYING,
    "value_mapping_undeclared": CATEGORICAL,
    "applicability_undeclared": APPLICABILITY,
    "orb_not_ratified": APPLICABILITY,
    "object_kind_not_covered_by_applicability": APPLICABILITY,
}
SOLVER = "solver_certificate"
REASON_GROUPS.update({
    "solver_budget_exhausted": SOLVER, "monotone_arc_not_established": SOLVER, "solver_certificate_incomplete": SOLVER,
    "verifier_budget_exhausted": SOLVER, "tie_isolation_unresolved": SOLVER, "tie_ambiguous": SOLVER})
#: the UNVERIFIED reasons the verifier's check demotes instead of blocking (R-6; restated, compared with `window_cert_check` by a test)
INCONCLUSIVE_REASONS = frozenset({"verifier_budget_exhausted", "tie_isolation_unresolved", "tie_ambiguous"})
#: the share of ALL windows that may be demoted: 0.5 % (R-6). Compared in integers (`demoted × 1000 > windows × 5`): no float edge.
INCONCLUSIVE_SHARE_CAP_PER_MILLE = 5
ALL_NULL_REASON = "all_null_candidate_policy"             # this module's own literal: under window_qualification/1 it can only mean a stub policy
DISCLOSURE = ("Under window_qualification/1 a window is NUMBERED (strength, peak and valence re-derived from its stored members through the frozen table the manifest binds) or "
              "BLANK with an explicit reason code. Blank windows are honest nulls — counted by reason here, never a refusal by themselves; a blank without a reason, a "
              "number the table does not yield, or a blank where it yields one is a refusal.")


class NumericalGateDisagrees(RuntimeError):
    """The independent re-derivation / recount of a grain's windows disagrees with what is stored (the verification job maps it to a DISAGREE)."""


class NumericalGateNotPassed(RuntimeError):
    """The generation has no PASSED numerical-window gate (the sealing job refuses by name)."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))


def table_binding() -> dict:
    from .input_vector_verifier import QUALIFICATION_TABLE_BINDING
    return dict(QUALIFICATION_TABLE_BINDING)


def reason_group(reason: str) -> str:
    return REASON_GROUPS.get(reason, OTHER)


def _rows(conn, sql, params=()):
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(sql, params).fetchall()]


def _has_provenance(conn) -> bool:
    n = _rows(conn, "SELECT count(*) FROM pg_attribute WHERE attrelid = 'public.ka_gochara_eval_window'::regclass AND attname = 'qualification' AND NOT attisdropped")
    return n[0][0] == 1


def census(conn, chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str) -> dict:
    """The stored windows of ONE grain, recounted by this module's own SQL: numbered (a peak is stored) vs blank (no peak) by reason, the valence of the numbered, and the
    structural problems (a blank with no reason, a reason on a numbered window, an unqualified-looking valence on a numbered one, a stub reason, a number on a blank)."""
    if not _has_provenance(conn):
        raise NumericalGateDisagrees("the window table carries no qualification provenance column: nothing here can name why a window is blank")
    rows = _rows(conn,
                 "SELECT (peak_instant IS NOT NULL), qualification ->> 'unqualified_reason', outcome_valence_for_native, (score IS NOT NULL),"
                 " (evidence_for IS NOT NULL OR evidence_against IS NOT NULL OR score IS NOT NULL OR objective_value IS NOT NULL), count(*)"
                 " FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = %s AND path_id = %s AND rule_version = %s"
                 " GROUP BY 1, 2, 3, 4, 5 ORDER BY 1, 2, 3, 4, 5", (chart_id, generation, event_class, path_id, rule_version))
    out: dict[str, Any] = {"windows": 0, "numbered": 0, "numbered_without_score": 0, "valence": {}, "blank": {}}
    problems: list[str] = []
    for numbered, reason, valence, has_score, has_number, n in rows:
        out["windows"] += n
        if numbered:
            out["numbered"] += n
            if not has_score:
                out["numbered_without_score"] += n
            out["valence"][valence] = out["valence"].get(valence, 0) + n
            if reason is not None:
                problems.append(f"{n} numbered window(s) also carry the blank reason {reason!r}")
            if valence == "unqualified":
                problems.append(f"{n} numbered window(s) carry the unqualified valence")
        else:
            if reason is None:
                problems.append(f"{n} blank window(s) carry NO reason code")
            elif reason == ALL_NULL_REASON:
                problems.append(f"{n} window(s) are blank under {ALL_NULL_REASON!r} — the all-NULL policy's reason under {POLICY_QUALIFICATION}: a stub policy")
            else:
                out["blank"][reason] = out["blank"].get(reason, 0) + n
            if has_number:
                problems.append(f"{n} blank window(s) carry a strength value but no peak")
            if valence != "unqualified":
                problems.append(f"{n} blank window(s) carry the valence {valence!r}")
    out["valence"] = dict(sorted(out["valence"].items()))
    out["blank"] = dict(sorted(out["blank"].items()))
    out["problems"] = problems
    return out


def demotions(report: dict) -> dict:
    """What the verifier's solver check demoted in a grain (R-6), from its re-derivation report: the windows that carried a number and could not be settled
    (`demoted`: reason → windows; `demoted_valence`: the valence the stored number carried → windows; `demoted_without_score`; `demoted_windows`: WHICH windows, as
    sorted `{window_id, reason}` — the serving path reads them back, so a demotion is a fact about named windows and not only a count) and the blanks it could not confirm."""
    dem: dict[str, int] = {}
    dem_valence: dict[str, int] = {}
    ids: list[dict] = []
    without_score = unconfirmed = 0
    for w in report.get("inconclusive_windows") or ():
        if w.get("stored_numbered"):
            if not isinstance(w.get("window_id"), str) or not w["window_id"]:
                raise NumericalGateDisagrees(f"a demoted window ({w.get('window')!r}) carries no stored window_id: what is demoted cannot be named, so it cannot be served as a blank")
            ids.append({"window_id": w["window_id"], "reason": w["reason"]})
            dem[w["reason"]] = dem.get(w["reason"], 0) + 1
            dem_valence[w["valence"]] = dem_valence.get(w["valence"], 0) + 1
            without_score += 0 if w.get("had_score") else 1
        else:
            unconfirmed += 1
    return {"demoted": dict(sorted(dem.items())), "demoted_valence": dict(sorted(dem_valence.items())), "demoted_without_score": without_score,
            "unconfirmed_blank_windows": unconfirmed, "demoted_windows": sorted(ids, key=lambda e: (e["window_id"], e["reason"]))}


def _after_classification(live: dict, d: dict) -> dict:
    """The attested populations: the STORED ones less the demoted numbered windows, which join the blanks under their named reason."""
    n = sum(d["demoted"].values())
    valence = dict(live["valence"])
    for v, k in d["demoted_valence"].items():
        valence[v] = valence.get(v, 0) - k
        if valence[v] == 0:
            del valence[v]
    blank = dict(live["blank"])
    for r, k in d["demoted"].items():
        blank[r] = blank.get(r, 0) + k
    return {"numbered": live["numbered"] - n, "numbered_without_score": live["numbered_without_score"] - d["demoted_without_score"],
            "valence": dict(sorted(valence.items())), "blank": dict(sorted(blank.items()))}


def _demoted_window_list_problems(d: dict) -> list[str]:
    """The attested `demoted_windows` must be a sorted list of `{window_id, reason}` that AGREES with the counts: one entry per demoted window, each id once, reasons
    counting up to `demoted`. (That each id is a stored numbered window of the grain is `generation_verdict`'s check, against the live table.)"""
    lst = d.get("demoted_windows")
    if not isinstance(lst, list) or not all(isinstance(e, dict) and set(e) == {"window_id", "reason"} and isinstance(e["window_id"], str) and e["window_id"]
                                            and isinstance(e["reason"], str) for e in lst):
        return ["the attested demoted_windows is not a list of {window_id, reason}"]
    out: list[str] = []
    ids = [e["window_id"] for e in lst]
    if len(set(ids)) != len(ids):
        out.append("a window is listed twice among the demoted windows")
    if lst != sorted(lst, key=lambda e: (e["window_id"], e["reason"])):
        out.append("the demoted windows are not listed in the sorted order")
    by_reason: dict[str, int] = {}
    for e in lst:
        by_reason[e["reason"]] = by_reason.get(e["reason"], 0) + 1
    if by_reason != dict(sorted(d["demoted"].items())):
        out.append(f"the demoted windows list {dict(sorted(by_reason.items()))!r} by reason; the attested counts are {dict(sorted(d['demoted'].items()))!r}")
    return out


def _numbered_window_ids(conn, chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str) -> set:
    """The window_ids of the grain's stored NUMBERED windows (a peak is stored), by this module's own SQL."""
    return {r[0] for r in _rows(conn, "SELECT window_id::text FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND event_class = %s"
                                      " AND path_id = %s AND rule_version = %s AND peak_instant IS NOT NULL ORDER BY 1",
                                (chart_id, generation, event_class, path_id, rule_version))}


def _demotion_problems(live: dict, d: dict) -> list[str]:
    out: list[str] = []
    n = sum(d["demoted"].values())
    if any(r not in INCONCLUSIVE_REASONS for r in d["demoted"]):
        out.append(f"windows were demoted under {sorted(r for r in d['demoted'] if r not in INCONCLUSIVE_REASONS)!r}: only {sorted(INCONCLUSIVE_REASONS)!r} may demote")
    if any(not isinstance(k, int) or isinstance(k, bool) or k < 0 for k in (*d["demoted"].values(), *d["demoted_valence"].values(), d["demoted_without_score"])):
        out.append("a demotion count is not a non-negative integer")
        return out
    out += _demoted_window_list_problems(d)
    if n != sum(d["demoted_valence"].values()):
        out.append(f"{n} window(s) demoted but their valences account for {sum(d['demoted_valence'].values())}")
    if n > live["numbered"] or any(k > live["valence"].get(v, 0) for v, k in d["demoted_valence"].items()) or d["demoted_without_score"] > min(n, live["numbered_without_score"]):
        out.append(f"{n} window(s) demoted but only {live['numbered']} are numbered (by valence {live['valence']!r}, {live['numbered_without_score']} without a score)")
    return out


def grain_attestation(conn, *, chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str, report: dict, policy: str) -> dict:
    """The attestation the verifier persists for ONE grain — built only after `verify_window_semantics` re-derived every window of it without a disagreement (it raises
    otherwise), and only when the independent recount agrees with that re-derivation AFTER CLASSIFICATION: the stored numbered windows are the reproduced numbered ones
    plus the demoted ones, and the demoted ones are attested as blanks under their named reason. Raises `NumericalGateDisagrees` on any difference."""
    tag = f"{event_class}/{path_id}@{rule_version}"
    if policy != POLICY_QUALIFICATION:
        raise NumericalGateDisagrees(f"{tag}: a numerical attestation is only given under {POLICY_QUALIFICATION}, not {policy!r}")
    if report.get("policy_version") != POLICY_QUALIFICATION:
        raise NumericalGateDisagrees(f"{tag}: the re-derivation ran under {report.get('policy_version')!r}, not {POLICY_QUALIFICATION}")
    c = census(conn, chart_id, generation, event_class, path_id, rule_version)
    problems = list(c["problems"])
    d = demotions(report)
    problems += _demotion_problems(c, d)
    if report.get("status") != "VERIFIED" or report.get("unverified_windows"):
        problems.append(f"the re-derivation is {report.get('status')!r} with {len(report.get('unverified_windows') or ())} window(s) it could not reproduce")
    if report.get("fully_reproduced") != c["windows"]:
        problems.append(f"{report.get('fully_reproduced')} of {c['windows']} stored windows were reproduced exactly")
    if report.get("numeric_reproduced", 0) + sum(d["demoted"].values()) != c["numbered"]:
        problems.append(f"the re-derivation reproduced {report.get('numeric_reproduced')} numbered windows and demoted {sum(d['demoted'].values())}; {c['numbered']} carry a peak")
    if problems:
        raise NumericalGateDisagrees(f"{tag}: " + "; ".join(problems))
    after = _after_classification(c, d)
    return {"schema": SCHEMA, "status": PASSED, "policy": POLICY_QUALIFICATION, "table": table_binding(), "windows": c["windows"], "reproduced": report["fully_reproduced"],
            **after, **d, "stored_numbered": c["numbered"]}


def runner_with_attestation(runner: dict, attestation: dict) -> dict:
    """The runner-identity object the 1240 row stores, carrying the attestation beside the commit / implementation digest the SQL gate reads."""
    return {**runner, ATTESTATION_KEY: attestation}


def generation_verdict(conn, chart_id: str, generation: str, classes=None) -> dict:
    """The gate's verdict for the generation, from the PERSISTED attestations and the LIVE stored windows — a pure read. NOT_APPLICABLE unless the manifest selects
    `window_qualification/1`. PASSED iff no problem: the manifest binds the frozen table, and every included P1–P4 grain has a VERIFIED 1240 row whose attestation is PASSED,
    names that table, and equals the live recount. `classes` limits it to a class subset (the job's own subset run)."""
    from .result_policy import manifest_vector
    vector = manifest_vector(conn, chart_id, generation)
    policy = None if vector is None else vector.get("result_policy")
    if policy != POLICY_QUALIFICATION:
        return {"schema": SCHEMA, "status": NOT_APPLICABLE, "policy": policy}
    binding = table_binding()
    problems: list[str] = []
    if vector.get("qualification_table") != binding:
        problems.append(f"the manifest binds qualification_table {vector.get('qualification_table')!r}; the verifier's frozen table is {binding!r}")
    pins = _rows(conn, "SELECT event_class, path_id, rule_version FROM public.ka_gochara_search_path_pin WHERE chart_id = %s AND generation = %s"
                       " AND disposition = 'included' AND path_id IN ('P1','P2','P3','P4') ORDER BY 1, 2, 3", (chart_id, generation))
    if classes is not None:
        pins = [p for p in pins if p[0] in set(classes)]
    verification = {(c, p, v): (s, pol, ws, ri if isinstance(ri, dict) else json.loads(ri)) for c, p, v, s, pol, ws, ri in _rows(
        conn, "SELECT event_class, path_id, rule_version, status, policy_version, windows_stored, runner_identity FROM public.ka_gochara_eval_window_verification"
              " WHERE chart_id = %s AND generation = %s", (chart_id, generation))}
    total = {"windows": 0, "numbered": 0, "numbered_without_score": 0, "demoted": 0, "unconfirmed_blank_windows": 0}
    demoted_by_reason: dict[str, int] = {}
    valence: dict[str, int] = {}
    by_path: dict[str, dict] = {}
    honest: dict[tuple, int] = {}
    for cls, path, ver in pins:
        tag = f"{cls}/{path}@{ver}"
        row = verification.get((cls, path, ver))
        if row is None:
            problems.append(f"{tag}: no window verification row")
            continue
        status, vpolicy, stored, runner = row
        att = runner.get(ATTESTATION_KEY)
        if status != "VERIFIED" or vpolicy != POLICY_QUALIFICATION:
            problems.append(f"{tag}: the window verification is {status!r} under {vpolicy!r}")
        if not isinstance(att, dict):
            problems.append(f"{tag}: the verification row carries no numerical-window attestation")
            continue
        try:
            live = census(conn, chart_id, generation, cls, path, ver)
        except NumericalGateDisagrees as exc:
            problems.append(f"{tag}: {exc}")
            continue
        problems += [f"{tag}: {p}" for p in live["problems"]]
        # R-6: the attested populations are the live (stored) ones after the verifier's classification. The demotions are the verifier's assertion (a stored row cannot
        # say it); everything else in the attestation must equal what the stored windows say now, and the demotions must fit inside the stored numbered windows.
        d = {"demoted": att.get("demoted", {}), "demoted_valence": att.get("demoted_valence", {}), "demoted_without_score": att.get("demoted_without_score", 0),
             "unconfirmed_blank_windows": att.get("unconfirmed_blank_windows", 0), "demoted_windows": att.get("demoted_windows", [])}
        shape = [f"{tag}: {p}" for p in _demotion_problems(live, d)] if all(isinstance(d[k], dict) for k in ("demoted", "demoted_valence")) else [f"{tag}: the attested demotions are malformed"]
        problems += shape
        if shape:
            continue
        # R-6 (lane review B-1): the serving path blanks exactly the windows listed here, so each must be a stored NUMBERED window of THIS grain — a listed id that is not
        # (a blank, a window of another grain, nothing at all) is a demotion of something that was never served as a number, and a numbered window left off the list is
        # one the counts say was demoted and nothing blanks
        stray = sorted({e["window_id"] for e in d["demoted_windows"]} - _numbered_window_ids(conn, chart_id, generation, cls, path, ver))
        if stray:
            problems.append(f"{tag}: the attested demoted windows {stray!r} are not stored numbered windows of this grain")
            continue
        after = _after_classification(live, d)
        want = {"schema": SCHEMA, "status": PASSED, "policy": POLICY_QUALIFICATION, "table": binding, "windows": live["windows"], "reproduced": live["windows"],
                **after, **d, "stored_numbered": live["numbered"]}
        if att != want:
            problems.append(f"{tag}: the persisted attestation {att!r} is not what the stored windows now say after classification {want!r}")
        if stored != live["windows"]:
            problems.append(f"{tag}: {stored} windows verified, {live['windows']} stored now")
        n_dem = sum(d["demoted"].values())
        total["windows"] += live["windows"]
        total["numbered"] += after["numbered"]
        total["numbered_without_score"] += after["numbered_without_score"]
        total["demoted"] += n_dem
        total["unconfirmed_blank_windows"] += d["unconfirmed_blank_windows"]
        for v, n in after["valence"].items():
            valence[v] = valence.get(v, 0) + n
        for r, n in d["demoted"].items():
            demoted_by_reason[r] = demoted_by_reason.get(r, 0) + n
        slot = by_path.setdefault(path, {"windows": 0, "numbered": 0, "blank": 0})
        slot["windows"] += live["windows"]
        slot["numbered"] += after["numbered"]
        slot["blank"] += live["windows"] - after["numbered"]
        for reason, n in after["blank"].items():
            honest[(path, reason)] = honest.get((path, reason), 0) + n
    blank = total["windows"] - total["numbered"]
    if total["demoted"] * 1000 > total["windows"] * INCONCLUSIVE_SHARE_CAP_PER_MILLE:
        problems.append(f"{total['demoted']} of {total['windows']} windows are demoted to a named blank (the verifier could not settle them): above the "
                        f"{INCONCLUSIVE_SHARE_CAP_PER_MILLE / 10:g} % cap — the seal refuses")
    return {"schema": SCHEMA, "status": FAILED if problems else PASSED, "policy": policy, "table": binding, "grains": len(pins), "windows": total["windows"],
            "numbered_windows": total["numbered"], "numbered_without_score": total["numbered_without_score"], "blank_windows": blank,
            "demoted_windows": total["demoted"], "demoted_by_reason": dict(sorted(demoted_by_reason.items())),
            "unconfirmed_blank_windows": total["unconfirmed_blank_windows"], "inconclusive_cap_per_mille": INCONCLUSIVE_SHARE_CAP_PER_MILLE,
            "valence_of_numbered": dict(sorted(valence.items())), "by_path": dict(sorted(by_path.items())),
            "honest_nulls": [{"path_id": p, "group": reason_group(r), "reason": r, "windows": n} for (p, r), n in sorted(honest.items())],
            "judgment_flags": (["no_window_numbered_under_numerical_policy"] if total["windows"] and not total["numbered"] else [])
            + (["windows_demoted_to_named_blank"] if total["demoted"] else []),
            "problems": problems, "disclosure": DISCLOSURE}


def require_passed(conn, chart_id: str, generation: str) -> dict:
    """The sealing job's check: raises `NumericalGateNotPassed` unless the verdict is PASSED (or the policy is not `window_qualification/1`)."""
    v = generation_verdict(conn, chart_id, generation)
    if v["status"] == FAILED:
        raise NumericalGateNotPassed(v["problems"])
    return v
