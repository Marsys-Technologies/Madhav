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

This module keeps its OWN literals (the frozen table's binding comes from the vector verifier's, not the builder's `result_policy`; a test asserts they are equal)."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "numerical_window_gate/1"
PASSED, FAILED, NOT_APPLICABLE = "PASSED", "FAILED", "NOT_APPLICABLE"
POLICY_QUALIFICATION = "window_qualification/1"
POLICY_ALL_NULL = "all_null_candidate/1"
ATTESTATION_KEY = "numerical_window_gate"                 # the key inside the 1240 row's runner_identity
SHARD_KEY = "verification_shard"                          # …beside it: WHICH launch (generation, head, image, execution, classes) wrote the row (SR-OD1 R8)

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


def grain_attestation(conn, *, chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str, report: dict, policy: str) -> dict:
    """The attestation the verifier persists for ONE grain — built only after `verify_window_semantics` re-derived every window of it without a disagreement (it raises
    otherwise), and only when the independent recount agrees with that re-derivation. Raises `NumericalGateDisagrees` on any difference."""
    tag = f"{event_class}/{path_id}@{rule_version}"
    if policy != POLICY_QUALIFICATION:
        raise NumericalGateDisagrees(f"{tag}: a numerical attestation is only given under {POLICY_QUALIFICATION}, not {policy!r}")
    if report.get("policy_version") != POLICY_QUALIFICATION:
        raise NumericalGateDisagrees(f"{tag}: the re-derivation ran under {report.get('policy_version')!r}, not {POLICY_QUALIFICATION}")
    c = census(conn, chart_id, generation, event_class, path_id, rule_version)
    problems = list(c["problems"])
    if report.get("status") != "VERIFIED" or report.get("unverified_windows"):
        problems.append(f"the re-derivation is {report.get('status')!r} with {len(report.get('unverified_windows') or ())} window(s) it could not reproduce")
    if report.get("fully_reproduced") != c["windows"]:
        problems.append(f"{report.get('fully_reproduced')} of {c['windows']} stored windows were reproduced exactly")
    if report.get("numeric_reproduced") != c["numbered"]:
        problems.append(f"the re-derivation reproduced {report.get('numeric_reproduced')} numbered windows; {c['numbered']} carry a peak")
    if problems:
        raise NumericalGateDisagrees(f"{tag}: " + "; ".join(problems))
    return {"schema": SCHEMA, "status": PASSED, "policy": POLICY_QUALIFICATION, "table": table_binding(), "windows": c["windows"], "reproduced": report["fully_reproduced"],
            "numbered": c["numbered"], "numbered_without_score": c["numbered_without_score"], "valence": c["valence"], "blank": c["blank"]}


def runner_with_attestation(runner: dict, attestation: dict, shard: dict | None = None) -> dict:
    """The runner-identity object the 1240 row stores, carrying the attestation beside the commit / implementation digest the SQL gate reads, and (a class-sharded
    launch, SR-OD1 R8) the shard stamp that says which launch wrote the row."""
    return {**runner, ATTESTATION_KEY: attestation, **({} if shard is None else {SHARD_KEY: shard})}


_IMAGE_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


def current_epoch(conn, chart_id: str, generation: str) -> str | None:
    """The EPOCH of a generation's build: the digest of the candidate manifest's identity and the search-input snapshot the verification reads. A rebuild replaces the manifest row
    and/or the snapshot, so every attestation written before it names another epoch and is void (R10-2). None when either is unreadable — an unreadable epoch is never matched."""
    pub = _rows(conn, "SELECT manifest_id::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", (chart_id, generation))
    snap = _rows(conn, "SELECT input_digest FROM public.ka_gochara_search_input_snapshot WHERE chart_id = %s AND generation = %s", (chart_id, generation))
    if len(pub) != 1 or len(snap) != 1:
        return None
    return hashlib.sha256(json.dumps({"generation": generation, "manifest_id": pub[0][0], "input_digest": snap[0][0]}, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def shard_stamp(*, generation: str, head: str, classes, epoch: str | None, image_digest: str | None = None, execution_id: str | None = None) -> dict:
    """What one verification launch (a SHARD: a class subset of the generation, or the whole of it) says about itself in every 1240 row it writes: the generation, the EPOCH it
    verified, the head (the commit of the code that ran), the immutable image digest and the execution, and the classes it verified. `generation_verdict` (the AGGREGATE) reads only these and
    the rows: a shard that ran at another head, or on another image, or for another generation, makes the aggregate refuse. Nothing here is a guess: a value the launch cannot
    name is None, and the aggregate says so."""
    return {"generation": generation, "epoch": epoch, "head": head, "image_digest": image_digest, "execution_id": execution_id, "classes": sorted(set(classes))}


def _shard_problems(tag: str, generation: str, cls: str, runner: dict, pinned_impl: str | None, epoch: str | None) -> list[str]:
    """Why ONE grain's row cannot be part of the aggregate: no shard stamp, a stamp for another generation, epoch or class, a head that is not the runner's own commit, an image
    digest or execution that is not named, or code the manifest did not pin (a shard run before a rebuild is void — R10-2)."""
    stamp = runner.get(SHARD_KEY)
    out = []
    if not isinstance(stamp, dict):
        return [f"{tag}: the verification row carries no shard stamp (it was not written by a stamped verification launch)"]
    if stamp.get("generation") != generation:
        out.append(f"{tag}: the shard attested generation {stamp.get('generation')!r}, not {generation!r}")
    if not isinstance(stamp.get("head"), str) or not stamp["head"] or stamp.get("head") != runner.get("commit"):
        out.append(f"{tag}: the shard head {stamp.get('head')!r} is not the commit {runner.get('commit')!r} of the runner that wrote the row")
    if epoch is None or stamp.get("epoch") != epoch:
        out.append(f"{tag}: the shard attested epoch {stamp.get('epoch')!r}; the generation's build epoch is {epoch!r} — it was rebuilt since, or its epoch is unreadable")
    if not (isinstance(stamp.get("image_digest"), str) and _IMAGE_DIGEST.fullmatch(stamp["image_digest"])):
        out.append(f"{tag}: the shard names no immutable image digest ({stamp.get('image_digest')!r})")
    if not (isinstance(stamp.get("execution_id"), str) and stamp["execution_id"].strip()):
        out.append(f"{tag}: the shard names no execution")
    if cls not in (stamp.get("classes") or []):
        out.append(f"{tag}: the shard that wrote the row does not list class {cls!r} among its classes")
    if pinned_impl is not None and runner.get("implementation_digest") != pinned_impl:
        out.append(f"{tag}: attested by code ({runner.get('implementation_digest')}) other than the code the manifest pins ({pinned_impl}) — a verification run before a rebuild is void")
    return out


def expected_classes(conn, chart_id: str, generation: str, vector: dict):
    """The class universe the aggregate must COVER: the manifest's pinned `scored_classes` (the pinned list, never 'whatever attestations exist'). A named seam: the G8 census
    opt-out of the older one-class job-mechanics suites (tests/l3/gochara/conftest.py) sets it aside, exactly as it sets aside the job's own census."""
    return vector.get("scored_classes")


def generation_verdict(conn, chart_id: str, generation: str, classes=None, head: str | None = None) -> dict:
    """The gate's verdict for the generation, from the PERSISTED attestations and the LIVE stored windows — a pure read. NOT_APPLICABLE unless the manifest selects
    `window_qualification/1`. PASSED iff no problem: the manifest binds the frozen table, and every included P1–P4 grain has a VERIFIED 1240 row whose attestation is PASSED,
    names that table, and equals the live recount. `classes` limits it to a class subset (the job's own subset run).

    With `classes=None` this is the AGGREGATE over class-sharded verification launches (SR-OD1 R8), the only verdict the seal brief and the sealing job read. It checks COVERAGE, not
    presence: every class the manifest pins (`scored_classes`) has its search-path pins and every included grain of it a PASSED attestation (a pinned class with no pin rows at all
    refuses); every row carries the shard stamp of the launch that wrote it (generation, head = the writing runner's commit, image digest, execution, classes); the rows agree on ONE
    head and ONE image (two shards at different heads refuse, naming both); and every row was written by the code the manifest pins (so a shard run before a rebuild that changed
    the code is void); every row is bound to the build EPOCH (manifest + search-input snapshot), a named image digest and a named execution; every pinned class has its search inventory
    and the inventory's independent re-derivation (the expected grains come from the inventories). `head`, when given, is the head the aggregate must be at. A subset verdict (`classes` given) is the job's own and does not carry these checks."""
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
    aggregate = classes is None
    pinned_impl = None
    if aggregate:
        from . import window_gate as wg
        impl = vector.get("implementation")
        pinned_impl = None if impl is None else hashlib.sha256(wg._canon(impl).encode("utf-8")).hexdigest()
        if pinned_impl is None:
            problems.append("the manifest vector pins no implementation: no shard can be shown to have run the pinned code")
        epoch = current_epoch(conn, chart_id, generation)
        # expected GRAINS come from the INVENTORIES: every pinned class needs its search inventory and that inventory's independent re-derivation (B3, SR-A10-1)
        inv = {r[0]: r[1] for r in _rows(conn, "SELECT event_class, inventory_digest FROM public.ka_gochara_search_inventory WHERE chart_id = %s AND generation = %s", (chart_id, generation))}
        inv_ver: dict[str, set] = {}
        for c, d in _rows(conn, "SELECT event_class, rederived_inventory_digest FROM public.ka_gochara_search_inventory_verification WHERE chart_id = %s AND generation = %s", (chart_id, generation)):
            inv_ver.setdefault(c, set()).add(d)
        scored = expected_classes(conn, chart_id, generation, vector)
        if not isinstance(scored, list) or not scored:
            problems.append("the manifest vector pins no scored_classes: the aggregate has no class census to cover")
            scored = []
        have = {p[0] for p in _rows(conn, "SELECT DISTINCT event_class FROM public.ka_gochara_search_path_pin WHERE chart_id = %s AND generation = %s", (chart_id, generation))}
        problems += [f"{c}: a pinned scored class with no search-path pin at all — no shard can have attested it" for c in sorted(set(scored) - have)]
        problems += [f"{c}: a class with search-path pins that the manifest does not pin as scored" for c in sorted(have - set(scored))]
        problems += [f"{c}: a pinned scored class with no search inventory — its grains cannot be enumerated" for c in sorted(set(scored) - set(inv))]
        problems += [f"{c}: the inventory is not attested by an independent re-derivation of its digest" for c in sorted(set(scored) & set(inv)) if inv_ver.get(c) != {inv[c]}]
    shards: dict[tuple, set] = {}
    executions: set[tuple] = set()
    total = {"windows": 0, "numbered": 0, "numbered_without_score": 0}
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
        if aggregate:
            problems += _shard_problems(tag, generation, cls, runner, pinned_impl, epoch)
            st = runner.get(SHARD_KEY)
            if isinstance(st, dict):
                shards.setdefault((st.get("head"), st.get("image_digest")), set()).add(cls)
                executions.add((st.get("execution_id"), st.get("head"), st.get("image_digest"), tuple(st.get("classes") or ())))
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
        want = {"schema": SCHEMA, "status": PASSED, "policy": POLICY_QUALIFICATION, "table": binding, "windows": live["windows"], "reproduced": live["windows"],
                "numbered": live["numbered"], "numbered_without_score": live["numbered_without_score"], "valence": live["valence"], "blank": live["blank"]}
        if att != want:
            problems.append(f"{tag}: the persisted attestation {att!r} is not what the stored windows now say {want!r}")
        if stored != live["windows"]:
            problems.append(f"{tag}: {stored} windows verified, {live['windows']} stored now")
        for k in total:
            total[k] += live[k]
        for v, n in live["valence"].items():
            valence[v] = valence.get(v, 0) + n
        slot = by_path.setdefault(path, {"windows": 0, "numbered": 0, "blank": 0})
        slot["windows"] += live["windows"]
        slot["numbered"] += live["numbered"]
        slot["blank"] += live["windows"] - live["numbered"]
        for reason, n in live["blank"].items():
            honest[(path, reason)] = honest.get((path, reason), 0) + n
    blank = total["windows"] - total["numbered"]
    extra: dict[str, Any] = {}
    if aggregate:
        heads = sorted({h for h, _ in shards}, key=str)
        images = sorted({i for _, i in shards}, key=str)
        if len(heads) > 1:
            problems.append("the classes were attested at different heads: " + "; ".join(f"{h!r}: {sorted(c for (hh, _), c2 in shards.items() if hh == h for c in c2)}" for h in heads))
        if len(images) > 1:
            problems.append("the classes were attested on different images: " + "; ".join(f"{i!r}: {sorted(c for (_, ii), c2 in shards.items() if ii == i for c in c2)}" for i in images))
        if head is not None and heads and heads != [head]:
            problems.append(f"the aggregate must be at head {head!r}; the shards ran at {heads}")
        extra = {"aggregate": {"head": heads[0] if len(heads) == 1 else None, "image_digest": images[0] if len(images) == 1 else None, "epoch": epoch,
                               "classes_attested": sorted(c for cs in shards.values() for c in cs),
                               "executions": [{"execution_id": e, "head": h, "image_digest": i, "classes": list(c)} for e, h, i, c in sorted(executions, key=str)]}}
    return {"schema": SCHEMA, "status": FAILED if problems else PASSED, "policy": policy, "table": binding, "grains": len(pins), "windows": total["windows"], **extra,
            "numbered_windows": total["numbered"], "numbered_without_score": total["numbered_without_score"], "blank_windows": blank,
            "valence_of_numbered": dict(sorted(valence.items())), "by_path": dict(sorted(by_path.items())),
            "honest_nulls": [{"path_id": p, "group": reason_group(r), "reason": r, "windows": n} for (p, r), n in sorted(honest.items())],
            "judgment_flags": ["no_window_numbered_under_numerical_policy"] if total["windows"] and not total["numbered"] else [],
            "problems": problems, "disclosure": DISCLOSURE}


def require_passed(conn, chart_id: str, generation: str) -> dict:
    """The sealing job's check: raises `NumericalGateNotPassed` unless the verdict is PASSED (or the policy is not `window_qualification/1`)."""
    v = generation_verdict(conn, chart_id, generation)
    if v["status"] == FAILED:
        raise NumericalGateNotPassed(v["problems"])
    return v
