"""G-6, COMPULSORY in the verifier's pinned plan (SR-OD1 R8X; A10.1 B5; PLAN_A10_1 §4, TRIAL_READY T18).

G-6 is the independent from-scratch re-solve of a sample of the function-valued numbered windows: no builder certificate is used, so a builder's bound that the verifier's own
enclosure does not honour cannot hide in a window the certificate check happened to accept. Until R8X it was a per-call option of the certificate check; it is now part of the
verifier's PINNED PLAN, and the generation-wide AGGREGATE (`numerical_window_gate.generation_verdict(classes=None)`) refuses a generation whose G-6 evidence is missing.

THE PLAN (`PLAN`, its sha256 `PLAN_DIGEST` is stored in every evidence object, so a verifier that ran another plan reads as a refusal):
  * POPULATION  every stored NUMBERED window that carries a builder `solver_certificate` in its `qualification` (the function-valued windows R-7 certifies);
  * SAMPLE      deterministic 3 %: window W is sampled iff the first 32 bits of sha256(window_key) / 2^32 < 0.03 (the seed rule IS the key; it is the rule of
                `window_cert_check.g6_sampled`, restated here — see `SAMPLE_RULE` — and compared with it by a test when that module is present);
  * TOP-MIXED   the generation-wide five windows whose certificates carry the most MIXED pieces (`geometry.pieces` entries of kind "mixed": the pieces the solver had to
                branch-and-bound), ties broken by window_key; always re-solved, whatever the sample says;
  * PASS        a selected window passes iff the from-scratch re-solve classifies it AGREED. DISAGREEMENT blocks the seal always (the verifier raises); INCONCLUSIVE or an
                unread result is "not shown" and the aggregate refuses (§N.8: nothing here is green unless a re-solve ran and agreed).

WHO RESOLVES. The from-scratch re-solve needs the window's records, factor rows and the sky: the production adapter is `window_verifier.g6_resolver` (SR-OD1 R8X S-1), which builds
`window_cert_check.check_numbered(resolve=True)`'s inputs from the stored rows the way the certificate check does and is bound by `verification_job` per grain. The contract this module fixes
(against R67's interface, `window_cert_check.CertReport`): a RESOLVER is `resolver(request: dict) -> report | None` with `request = {"resolve": True, "window_key", "window_id", "event_class",
"path_id", "rule_version", "chart_id", "generation", "selected_by"}`; the report has `.classification` in AGREED / DISAGREEMENT / INCONCLUSIVE (None: the resolver does not cover the window).
A resolver that covers nothing records every selected window as unresolved and the aggregate refuses.

(I) INTERPRETATIONS: "generation-wide top-five mixed pieces" is read as the five WINDOWS with the most mixed pieces (alternative: the five widest mixed pieces); a window that is both
sampled and top-mixed is re-solved once and carries both reasons; the population is read from stored `solver_certificate`s (a numbered function-valued window WITHOUT one is refused by the
certificate check itself, not sampled here)."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Optional

SCHEMA = "g6_evidence/1"
KEY = "g6_evidence"                       # the key inside the 1240 row's runner_identity (beside the numerical attestation and the shard stamp)
SAMPLE_PER_MILLE = 30                     # the stored / briefed form (the brief has no float encoding)
SAMPLE_RATE = SAMPLE_PER_MILLE / 1000     # PLAN_A10_1 §4: deterministic 3 % (the certificate check's own default is 2 %: the plan passes this rate explicitly)
TOP_MIXED = 5
PASS_CLASS = "AGREED"
SAMPLE_RULE = "sha256(window_key)[:8] / 2**32 < rate"
KEY_FORMAT = "chart_id|generation|event_class|path_id|rule_version|interval_lower_utc|interval_upper_utc"
PLAN = {"schema": "g6_plan/1", "population": "numbered windows carrying qualification.solver_certificate", "sample_per_mille": SAMPLE_PER_MILLE, "sample_rule": SAMPLE_RULE,
        "window_key": KEY_FORMAT, "top_mixed": TOP_MIXED, "top_mixed_rank": "count of geometry.pieces of kind 'mixed' desc, window_key asc", "pass": PASS_CLASS}
PLAN_DIGEST = hashlib.sha256(json.dumps(PLAN, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
BY_SAMPLE, BY_TOP = "sample", "top_mixed"

Resolver = Callable[[dict], Optional[object]]


def window_key(chart_id: str, generation: str, event_class: str, path_id: str, rule_version: str, lower: str, upper: str) -> str:
    return "|".join((chart_id, generation, event_class, path_id, rule_version, lower, upper))


def sampled(key: str, rate: float = SAMPLE_RATE) -> bool:
    """The deterministic G-6 sample (the rule of `window_cert_check.g6_sampled`, at the PLAN's rate)."""
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest()[:8], 16) / 4294967296.0 < rate


def count_mixed(pieces: Any) -> int:
    """How many mixed pieces a certificate's `geometry.pieces` records (0 when it records none or is malformed — a malformed certificate is the certificate check's refusal, not a rank).
    A piece is `[a, b_eff, kind]` (`window_solver`'s trace)."""
    if not isinstance(pieces, list):
        return 0
    return sum(1 for p in pieces if isinstance(p, (list, tuple)) and len(p) == 3 and p[2] == "mixed")


def mixed_pieces(qualification: Any) -> int:
    """`count_mixed` of the window's stored certificate (`qualification.solver_certificate.geometry.pieces`)."""
    cert = qualification.get("solver_certificate") if isinstance(qualification, dict) else None
    return count_mixed(((cert or {}).get("geometry") or {}).get("pieces") if isinstance(cert, dict) else None)


def _iso(ts) -> str:
    return ts if isinstance(ts, str) else ts.isoformat()


def population(conn, chart_id: str, generation: str) -> list[dict]:
    """Every numbered, certificate-bearing window of the generation, in a total order: {key, window_id, grain, mixed}. A pure read of the stored windows."""
    rows = conn.execute(
        "SELECT window_id::text, event_class, path_id, rule_version, to_char(lower(interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'),"
        " to_char(upper(interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"'), qualification #> '{solver_certificate,geometry,pieces}'"
        " FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s AND peak_instant IS NOT NULL AND qualification -> 'solver_certificate' IS NOT NULL"
        " ORDER BY event_class, path_id, rule_version, lower(interval), upper(interval), window_id", (chart_id, generation)).fetchall()
    out = []
    for r in rows:
        wid, cls, path, ver, lo, hi, pieces = tuple(r.values()) if isinstance(r, dict) else tuple(r)
        pieces = json.loads(pieces) if isinstance(pieces, str) else pieces
        out.append({"key": window_key(chart_id, generation, cls, path, ver, lo, hi), "window_id": wid, "grain": (cls, path, ver), "mixed": count_mixed(pieces)})
    return out


class Selection:
    """What the plan REQUIRES of the generation, recomputed from the stored windows (never from the evidence): per grain the population count and the selected windows with their reasons."""

    def __init__(self, windows: list[dict]):
        ranked = sorted((w for w in windows if w["mixed"] > 0), key=lambda w: (-w["mixed"], w["key"]))[:TOP_MIXED]
        self.top_mixed = [w["key"] for w in ranked]
        self.population: dict[tuple, int] = {}
        self.required: dict[tuple, dict[str, dict]] = {}
        for w in windows:
            g = w["grain"]
            self.population[g] = self.population.get(g, 0) + 1
            why = sorted(([BY_SAMPLE] if sampled(w["key"]) else []) + ([BY_TOP] if w["key"] in self.top_mixed else []))
            if why:
                self.required.setdefault(g, {})[w["key"]] = {"window_id": w["window_id"], "selected_by": why}
        self.total = len(windows)

    def for_grain(self, grain: tuple) -> dict[str, dict]:
        return self.required.get(tuple(grain), {})

    def summary(self) -> dict:
        sampled_n = sum(1 for g in self.required.values() for v in g.values() if BY_SAMPLE in v["selected_by"])
        return {"plan_digest": PLAN_DIGEST, "sample_per_mille": SAMPLE_PER_MILLE, "population": self.total, "sampled": sampled_n, "top_mixed": list(self.top_mixed)}


def selection(conn, chart_id: str, generation: str) -> Selection:
    return Selection(population(conn, chart_id, generation))


def collect(*, chart_id: str, generation: str, grain: dict, sel: Selection, resolver: Optional[Resolver]) -> dict:
    """The G-6 evidence of ONE grain: the plan digest, the grain's population, and for every window the plan selects its re-solve result (None when no resolver ran or covered it).
    A re-solve that DISAGREES raises (the verification job maps it to a DISAGREE): the seal is blocked, always."""
    g = (grain["event_class"], grain["path_id"], grain["rule_version"])
    tag = f"{g[0]}/{g[1]}@{g[2]}"
    results: dict[str, dict] = {}
    for key, info in sorted(sel.for_grain(g).items()):
        report = None if resolver is None else resolver({"resolve": True, "window_key": key, "window_id": info["window_id"], "event_class": g[0], "path_id": g[1],
                                                         "rule_version": g[2], "chart_id": chart_id, "generation": generation, "selected_by": list(info["selected_by"])})
        cls = None if report is None else report.classification
        if cls == "DISAGREEMENT":
            codes = "; ".join(f"{c}: {d}" for c, d in getattr(report, "findings", ()))
            raise RuntimeError(f"{tag}: the G-6 from-scratch re-solve of window {info['window_id']} DISAGREES with the stored window — {codes}")
        results[key] = {"window_id": info["window_id"], "selected_by": list(info["selected_by"]), "result": cls}
    return {"schema": SCHEMA, "plan_digest": PLAN_DIGEST, "sample_per_mille": SAMPLE_PER_MILLE, "population": sel.population.get(g, 0), "windows": results}


def evidence_problems(tag: str, evidence: Any, grain: tuple, sel: Selection) -> list[str]:
    """Why a grain's stored G-6 evidence does not meet the plan, judged against the selection recomputed from the live windows. Empty iff the evidence is present, is for this plan,
    counts the live population, covers exactly the windows the plan selects (a missing one or an extra one both refuse) and every one re-solved AGREED."""
    if not isinstance(evidence, dict):
        return [f"{tag}: the verification row carries no G-6 evidence (the compulsory sample was not drawn)"]
    out = []
    if evidence.get("schema") != SCHEMA or evidence.get("plan_digest") != PLAN_DIGEST:
        out.append(f"{tag}: the G-6 evidence is for plan {evidence.get('plan_digest')!r}, not the pinned plan {PLAN_DIGEST!r}")
    if evidence.get("population") != sel.population.get(tuple(grain), 0):
        out.append(f"{tag}: the G-6 evidence counts {evidence.get('population')!r} certified window(s); {sel.population.get(tuple(grain), 0)} are stored now")
    have = evidence.get("windows") if isinstance(evidence.get("windows"), dict) else {}
    want = sel.for_grain(grain)
    for key in sorted(set(want) - set(have)):
        out.append(f"{tag}: window {want[key]['window_id']} ({'+'.join(want[key]['selected_by'])}) is selected by the G-6 plan but has no re-solve")
    for key in sorted(set(have) - set(want)):
        out.append(f"{tag}: the G-6 evidence names window {(have[key] or {}).get('window_id')!r}, which the plan does not select now")
    for key in sorted(set(want) & set(have)):
        res = (have[key] or {}).get("result") if isinstance(have[key], dict) else None
        if res != PASS_CLASS:
            out.append(f"{tag}: the G-6 re-solve of window {want[key]['window_id']} ({'+'.join(want[key]['selected_by'])}) is {res!r}, not {PASS_CLASS}")
        elif sorted((have[key] or {}).get("selected_by") or ()) != want[key]["selected_by"]:
            out.append(f"{tag}: the G-6 evidence gives window {want[key]['window_id']} the reasons {have[key].get('selected_by')!r}; the plan gives {want[key]['selected_by']!r}")
    return out


__all__ = ["BY_SAMPLE", "BY_TOP", "KEY", "PLAN", "PLAN_DIGEST", "SAMPLE_PER_MILLE", "SAMPLE_RATE", "SCHEMA", "TOP_MIXED", "Selection", "collect", "evidence_problems", "mixed_pieces",
           "population", "sampled", "selection", "window_key"]
