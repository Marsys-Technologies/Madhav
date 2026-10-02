"""The SEAL BRIEF and its canonical COMPLETE APPROVAL PAYLOAD (Codex round 11, R11-3; schema agreed with Stream B in
`SEAL_APPROVAL_PAYLOAD_v1_0.md`).

What is approved must be what is sealed. A gate result alone cannot say that — two different valid candidates can both give an
empty gate. The verifier-run BRIEF therefore evaluates the candidate adapter gate, reads the PERSISTED attestations, and hashes
ONE canonical payload (`seal_approval_payload/1`) that contains, besides the gate and the attestations, the GENERATION-WIDE OUTPUT
IDENTITY — a digest over every record, prerequisite, contact, window, member link, path pin and inventory header of the generation
(every column, including held and superseded-version rows; only `created_at` is excluded) — plus the manifest identity, the
policies, the runner/code identity, the migration-ledger evidence and the disclosures. The approval carries that sha256. The
SEALING step calls `recompute_under_locks` under the seal locks, in the publishing transaction, and refuses on any difference:
a candidate changed after the brief — even one whose gate is still empty — invalidates the approval.

ONE canonical implementation: the brief and the sealer both call `build_payload`; nothing here commits or opens a connection.
Read-only (SELECT + the gate functions); it takes the two seal locks (re-entrant) and holds nothing else.

Trust boundary, stated squarely: the approval is NOT an independent human check (native ruling #2). The brief guarantees that the
candidate adapter found no violation, that every included grain is VERIFIED by the separate job under a runner pinned to the
manifest, that the exact output shown is the output sealed (the identity digest), and — in the sealing transaction — that the
authoritative SQL seal checks pass on the published row. A seal is not a flip."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "seal_approval_payload/1"
SEAL_IS_NOT_A_FLIP = "A seal is not a flip: sealing a generation publishes it for replay and serves nothing."
#: the migrations whose ledger evidence the payload carries (filename prefix)
LEDGER_MIGRATIONS = ("1204", "1206", "1232", "1233", "1240", "1241")
_DIGEST = re.compile(r"^[0-9a-f]{64}\Z")

#: the generation-scoped output tables the identity digest covers, with a stable per-table ordering
OUTPUT_TABLES = (
    "ka_gochara_relationship_record", "ka_gochara_record_prerequisite", "ka_gochara_contact", "ka_gochara_eval_window",
    "ka_gochara_eval_window_record", "ka_gochara_search_path_pin", "ka_gochara_search_inventory",
    # F-R12-2 (independent review): the inventory's own inputs are bound ROW BY ROW as well, not only through the inventory/ledger
    # digests — the search-input snapshot, the committed obligations and the interval ledger
    "ka_gochara_search_input_snapshot", "ka_gochara_search_obligation", "ka_gochara_search_interval")
_VERIFICATION_TABLES = ("ka_gochara_eval_window_verification", "ka_gochara_search_inventory_verification")


class BriefRefused(RuntimeError):
    """No brief is produced: the candidate is not in a state that can be approved. `violations` names why."""

    def __init__(self, code: str, detail: str, violations: list | None = None):
        super().__init__(f"brief refused:{code} — {detail}")
        self.code, self.detail, self.violations = code, detail, list(violations or [])


class ApprovalMismatch(RuntimeError):
    """The payload recomputed under the seal locks is not the one that was approved."""


class NotCanonicallyEncodable(TypeError):
    """A value of a type the strict canonical serializer has no explicit rule for (F-R13-6)."""


def canonical_json(v, _path: str = "$", *, ascii_only: bool = False) -> str:
    """The STRICT canonical JSON of the approval payload and everything displayed with it (F-R13-6): sorted keys (code point), no
    whitespace, UTF-8 unescaped — and EVERY type is encoded by an explicit rule or REFUSED, so a digest (or a displayed brief) can never
    depend on `str()` of something unforeseen. Rules: None/bool/int/str as JSON; Decimal (finite only) as a plain-notation JSON number;
    UUID as its lowercase hyphenated string; an aware datetime as UTC ISO-8601 with microseconds and `Z` (a naive one is refused); a
    date as ISO-8601; dict (string keys only) and list/tuple recursively. float, bytes, set, NaN/Infinity, naive datetimes, non-string
    keys and anything else raise `NotCanonicallyEncodable` naming the path. For the types the payload actually carries the output is
    byte-identical to `window_gate._canon` (the form every existing digest was computed in). `ascii_only=True` escapes every non-ASCII
    character (`\\uXXXX`, as `json.dumps` does by default) — the DISPLAY form of the brief line, so that characters equal bytes."""
    import datetime as _dt
    import uuid as _uuid
    from decimal import Decimal
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, Decimal):
        if not v.is_finite():
            raise NotCanonicallyEncodable(f"{_path}: a non-finite Decimal ({v}) has no canonical JSON")
        return format(v, "f")
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=ascii_only)
    if isinstance(v, _uuid.UUID):
        return json.dumps(str(v), ensure_ascii=ascii_only)
    if isinstance(v, _dt.datetime):
        if v.tzinfo is None or v.utcoffset() is None:
            raise NotCanonicallyEncodable(f"{_path}: a naive datetime has no canonical JSON (an instant needs a zone)")
        return json.dumps(v.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"))
    if isinstance(v, _dt.date):
        return json.dumps(v.isoformat())
    if isinstance(v, dict):
        bad = [k for k in v if not isinstance(k, str)]
        if bad:
            raise NotCanonicallyEncodable(f"{_path}: object keys must be strings, got {type(bad[0]).__name__}")
        return "{" + ",".join(json.dumps(k, ensure_ascii=ascii_only) + ":" + canonical_json(v[k], f"{_path}.{k}", ascii_only=ascii_only) for k in sorted(v)) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(canonical_json(x, f"{_path}[{i}]", ascii_only=ascii_only) for i, x in enumerate(v)) + "]"
    raise NotCanonicallyEncodable(f"{_path}: {type(v).__name__} has no canonical JSON rule (floats, bytes, sets and unknown types are refused)")


_canon = canonical_json


def payload_digest(payload: dict) -> str:
    return hashlib.sha256(_canon(payload).encode("utf-8")).hexdigest()


# ── transport of the DISPLAY brief (F-R13-2; the contract agreed with Stream B, steward M20261002T174919) ───────────
# The brief line T = {"brief": <payload>, "persisted": {brief_id, manifest_id, state_digest}, "sha256": <digest>} — sorted keys, compact,
# ASCII (characters = bytes). If T fits `BRIEF_SINGLE_LINE_MAX` it is printed unchanged; otherwise it is printed as N lines of
# {"brief_chunk": {"data", "index", "sha256": sha256(T), "total"}} with `CHUNK_CHARS`-char slices (Stream B's extractor reassembles and
# verifies; their `chunk_brief` is the parity oracle). The full brief grows with the event-class count (~10 KB per class + ~8 KB fixed).
BRIEF_SINGLE_LINE_MAX = 200_000
CHUNK_CHARS = 60_000


def brief_line(result: dict, persisted: dict) -> str:
    """T — built by the strict serializer, and REFUSED unless parsing it back (decimals kept exact) re-derives the payload digest it
    carries: what is displayed can never differ from what was digested (F-R13-6)."""
    from decimal import Decimal
    text = canonical_json({"brief": result["payload"], "persisted": persisted, "sha256": result["sha256"]}, ascii_only=True)
    if not text.isascii():
        raise BriefRefused("brief_line_not_ascii", "the brief line is not ASCII")
    back = json.loads(text, parse_float=Decimal)
    if payload_digest(back["brief"]) != result["sha256"]:
        raise BriefRefused("brief_line_digest_mismatch", "the brief line does not re-derive the digest it carries")
    return text


def emit_lines(text: str, *, single_max: int | None = None, size: int | None = None) -> list[str]:
    """The stdout lines that carry T: `[T]` when `len(T) <= single_max`, else the chunk lines (sorted keys, compact separators)."""
    single_max = BRIEF_SINGLE_LINE_MAX if single_max is None else single_max
    size = CHUNK_CHARS if size is None else size
    if not text or size < 1:
        raise ValueError("nothing to emit")
    if len(text) <= single_max:
        return [text]
    whole = hashlib.sha256(text.encode("utf-8")).hexdigest()
    pieces = [text[i:i + size] for i in range(0, len(text), size)]
    return [json.dumps({"brief_chunk": {"data": piece, "index": i, "sha256": whole, "total": len(pieces)}}, sort_keys=True,
                       separators=(",", ":")) for i, piece in enumerate(pieces)]


def _rows(conn, sql, params=()) -> list[tuple]:
    return [tuple(r.values()) if isinstance(r, dict) else tuple(r) for r in conn.execute(sql, params).fetchall()]


def generation_output_identity(conn, chart_id: str, generation: str) -> dict:
    """ONE digest over ALL output of the generation: for each output table, the sha256 over its rows (`to_jsonb(row)` minus
    `created_at`, one canonical line per row, ordered by that text) — every column, every grain, held and superseded-version
    rows included — and the digest of those per-table digests. Any row added, removed or altered anywhere changes it."""
    tables: dict[str, Any] = {}
    for t in OUTPUT_TABLES:
        h, n = hashlib.sha256(), 0
        for (line,) in _rows(conn, f"SELECT j::text FROM (SELECT to_jsonb(t) - 'created_at' AS j FROM public.{t} t"
                                   " WHERE t.chart_id = %s AND t.generation = %s) x ORDER BY j::text", (chart_id, generation)):
            h.update(line.encode("utf-8"))
            h.update(b"\n")
            n += 1
        tables[t] = {"rows": n, "sha256": h.hexdigest()}
    return {"tables": tables, "sha256": hashlib.sha256(_canon(tables).encode("utf-8")).hexdigest()}


def _attestations(conn, chart_id: str, generation: str) -> dict:
    """The PERSISTED attestations, as stored (read, never re-derived)."""
    out: dict[str, Any] = {}
    for t in _VERIFICATION_TABLES:
        out[t] = [line for (line,) in _rows(
            conn, f"SELECT j::text FROM (SELECT to_jsonb(t) AS j FROM public.{t} t WHERE t.chart_id = %s AND t.generation = %s)"
                  " x ORDER BY j::text", (chart_id, generation))]
    return out


def _ledger_evidence(conn) -> list[dict]:
    rows = _rows(conn, "SELECT filename, sha256, applied_at FROM public._migrations_applied ORDER BY filename")
    out = []
    for prefix in LEDGER_MIGRATIONS:
        hit = [r for r in rows if r[0].startswith(prefix + "_") or r[0].startswith(prefix + ".")]
        out.append({"migration": prefix,
                    "applied": [{"filename": f, "sha256": s, "applied_at": None if a is None else a.isoformat()}
                                for f, s, a in hit]})
    return out


#: the session settings that change how timestamps, intervals, ranges and floats RENDER as text — pinned for every computation of the
#: payload / publication digest so a verifier session and a sealer session in different settings still agree (F-R12-6)
PINNED_SETTINGS = (("TimeZone", "UTC"), ("DateStyle", "ISO, YMD"), ("IntervalStyle", "iso_8601"), ("extra_float_digits", "1"))


from contextlib import contextmanager


@contextmanager
def pinned_session(conn):
    """Pin the text-rendering session settings for the duration of the block (transaction-local), and RESTORE the caller's values at
    exit — so the digest cannot depend on the session that computes it, and the caller's session is left as it was."""
    with conn.transaction():
        prev = {k: _rows(conn, "SELECT current_setting(%s)", (k,))[0][0] for k, _ in PINNED_SETTINGS}
        for k, v in PINNED_SETTINGS:
            conn.execute("SELECT set_config(%s, %s, true)", (k, v))
        yield                      # (an exception rolls the savepoint back, which reverts the transaction-local settings by itself)
        for k, v in prev.items():
            conn.execute("SELECT set_config(%s, %s, true)", (k, v))


def build_payload(conn, chart_id: str, generation: str, *, sealing_commit: str | None = None,
                  as_candidate: bool = False) -> dict:
    """See `_build_payload`; computed inside `pinned_session` (F-R12-6)."""
    with pinned_session(conn):
        return _build_payload(conn, chart_id, generation, sealing_commit=sealing_commit, as_candidate=as_candidate)


def _build_payload(conn, chart_id: str, generation: str, *, sealing_commit: str | None = None,
                   as_candidate: bool = False) -> dict:
    """The canonical COMPLETE approval payload (`seal_approval_payload/1`). Pure reads. The caller decides whether a violation
    is fatal (`brief` refuses; the sealer's recompute compares digests). `as_candidate=True` is for the post-PUBLICATION re-check
    inside the sealing transaction: the manifest's own publication fields (status, the digest/counts publication fills in) are
    normalised, so the result is comparable with the pre-publication payload — everything else must be byte-identical."""
    from . import candidate_boundary as cb
    from . import verification_job as vj
    from . import window_gate as wg
    from .result_policy import manifest_policy
    pub = _rows(conn, "SELECT manifest_id::text, status, horizon::text, convention_id, input_generation_vector::text,"
                      " writer_asset_id, ephemeris_backend::text FROM public.kala_gochara_publication"
                      " WHERE chart_id = %s AND generation = %s", (chart_id, generation))
    if not pub:
        raise BriefRefused("no_candidate_manifest", f"generation {generation} has no manifest")
    manifest_id, status, horizon, convention, vector_text, writer_asset, backend_text = pub[0]
    import json
    from decimal import Decimal
    vector = json.loads(vector_text, parse_float=Decimal)
    backend = json.loads(backend_text, parse_float=Decimal)
    violations = vj.candidate_gate_on_candidate_manifest(conn, chart_id, generation)
    classes = []
    for cls, inv_digest, led_digest in _rows(conn, "SELECT event_class, inventory_digest, ledger_digest FROM"
                                                   " public.ka_gochara_search_inventory WHERE chart_id = %s AND generation = %s"
                                                   " ORDER BY event_class", (chart_id, generation)):
        grains = _rows(conn, "SELECT path_id, rule_version, status, policy_version, windows_content_digest,"
                             " expected_windows_digest, derivation_inputs_digest, verified_at::text, verifier_id,"
                             " verifier_version, runner_identity::text FROM public.ka_gochara_eval_window_verification"
                             " WHERE chart_id = %s AND generation = %s AND event_class = %s ORDER BY path_id, rule_version",
                       (chart_id, generation, cls))
        classes.append({"event_class": cls, "inventory_digest": inv_digest, "ledger_digest": led_digest, "grains": [
            {"path_id": p, "rule_version": v, "status": s, "verifier_policy_version": pol, "windows_content_digest": wc,
             "expected_windows_digest": we, "derivation_inputs_digest": di, "verified_at": at,
             "verifier": f"{vid}@{vver}", "runner": {k: json.loads(rid)[k] for k in ("commit", "implementation_digest")}}
            for p, v, s, pol, wc, we, di, at, vid, vver, rid in grains]})
    runners = {(g["runner"]["commit"], g["runner"]["implementation_digest"]) for c in classes for g in c["grains"]}
    pinned = hashlib.sha256(_canon(vector["implementation"]).encode("utf-8")).hexdigest()
    return {
        "schema": SCHEMA, "chart_id": chart_id, "generation": generation,
        "manifest": {"manifest_id": manifest_id, "status": "candidate" if as_candidate else status, "horizon": horizon,
                     "convention_id": convention, "writer_asset_id": writer_asset,
                     "ephemeris_backend": backend,
                     "input_generation_vector_digest": hashlib.sha256(_canon(vector).encode("utf-8")).hexdigest()},
        "result_policy": manifest_policy(conn, chart_id, generation),
        "candidate_gate": {"source": "candidate_adapter/1 over ka_gochara_candidate_gate_violations",
                           "violations": sorted((f"{v['event_class']}/{v['path_id']}@{v['rule_version']}:{v['violation']}"
                                                 for v in violations))},
        "classes": classes,
        "attestations": _attestations(conn, chart_id, generation),
        "generation_output_identity": generation_output_identity(conn, chart_id, generation),
        # R12-1: the rest of the CANDIDATE BOUNDARY (candidate_boundary.py): build coverage, the legacy projection relations (none may
        # exist), the exact digest publication will store, and the explicit covered / not-covered statement
        "coverage_identity": cb.coverage_identity(conn, chart_id, generation),
        "legacy_projection": {**cb.legacy_projection_counts(conn, chart_id, generation),
                              "policy": "none may exist for a governed generation"},
        "publication_content_digest": cb.publication_content_digest(conn, chart_id, generation),
        "boundary": cb.boundary_statement(),
        "code": {"verification_runners": sorted([{"commit": c, "implementation_digest": d} for c, d in runners],
                                                key=lambda r: (r["commit"], r["implementation_digest"])),
                 "manifest_pinned_implementation_digest": pinned, "sealing_commit": sealing_commit},
        "ledger": _ledger_evidence(conn),
        "disclosures": {"policy": _policy_disclosure(manifest_policy(conn, chart_id, generation)),
                        "named_limits": __import__("services.gochara_kernel.scope_response", fromlist=["x"]).named_limits(),
                        "attestation_binding": "composition: inputs/2 per grain + DB-guarded path pins + the 1206 inventory "
                                               "verification row + the generation-wide output identity above",
                        "candidate_adapter": "three published-only completeness arms are re-derived against the candidate "
                                             "manifest; the authoritative gate is the seal's, on the published row"},
        "seal_is_not_a_flip": SEAL_IS_NOT_A_FLIP,
    }


ALL_NULL_POLICY = "all_null_candidate/1"


def _policy_disclosure(policy: str) -> str:
    """The disclosure's wording follows the MANIFEST's policy name — it never asserts the all-NULL claim for a manifest that selects
    another policy (F-R13 / Stream B): `no numerical result exists` is said only under `all_null_candidate/1`, where the window CHECKs and
    the generation-wide gate (including the legacy-row arm) enforce it."""
    if policy == ALL_NULL_POLICY:
        return (f"{policy} — no numerical result exists in this generation: the policy forbids one (window all-NULL arms) and the "
                "legacy projection relations hold none (enforced by the gate, not assumed)")
    return f"{policy} — this brief makes no all-NULL claim; the result policy above governs what this generation may contain"


def _current_and_complete(payload: dict) -> list[str]:
    """Why this candidate cannot be briefed (empty = it can): a gate violation, a grain that is not VERIFIED, a class with no
    attestation at all, a runner that is not the manifest's pinned code."""
    problems = list(payload["candidate_gate"]["violations"])
    if not payload["classes"]:
        problems.append("the generation has no search inventory")
    for c in payload["classes"]:
        if not c["grains"]:
            problems.append(f"{c['event_class']}: no window verification persisted")
        for g in c["grains"]:
            if g["status"] != "VERIFIED":
                problems.append(f"{c['event_class']}/{g['path_id']}@{g['rule_version']}: {g['status']}")
            if g["runner"]["implementation_digest"] != payload["code"]["manifest_pinned_implementation_digest"]:
                problems.append(f"{c['event_class']}/{g['path_id']}: runner is not the manifest's pinned code")
    if not payload["attestations"]["ka_gochara_search_inventory_verification"]:
        problems.append("no inventory verification row persisted")
    for table, n in payload["legacy_projection"].items():
        if table != "policy" and n:
            problems.append(f"{n} legacy {table} row(s) exist for this generation — none may (the '5.0' writer writes none)")
    if payload["manifest"]["status"] != "candidate":
        problems.append(f"the manifest is {payload['manifest']['status']!r}, not a candidate")
    return problems


def brief(conn, chart_id: str, generation: str, *, sealing_commit: str | None = None) -> dict:
    """The verifier-run brief: `{"payload", "sha256"}`. REFUSES (BriefRefused, naming each reason) unless the candidate adapter
    returns no violation and every attestation is persisted, VERIFIED and pinned. Takes the seal locks so the payload is a
    consistent read; the locks end with the caller's transaction."""
    vj_lock(conn, chart_id)
    payload = build_payload(conn, chart_id, generation, sealing_commit=sealing_commit)
    problems = _current_and_complete(payload)
    if problems:
        raise BriefRefused("candidate_not_approvable", "; ".join(problems), problems)
    return {"payload": payload, "sha256": payload_digest(payload)}


def persist_brief(conn, result: dict) -> dict:
    """F-R12-4: persist the brief the VERIFIER just produced (`brief()`'s result) in `ka_gochara_seal_brief`, inside the same transaction
    that holds the seal locks. The database attests the manifest, the state digest, the session login and the time (whatever this INSERT
    carries for them is overwritten); the receipt a seal writes must name this digest. Returns `{brief_id, manifest_id, state_digest}`."""
    from . import window_gate as wg
    payload = result["payload"]
    row = conn.execute(
        "INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest, runner_identity)"
        " VALUES (%s::uuid, %s, %s::uuid, %s, repeat('0', 64), %s::jsonb) RETURNING brief_id, manifest_id::text, state_digest",
        (payload["chart_id"], payload["generation"], payload["manifest"]["manifest_id"], result["sha256"],
         _canon({k: wg.runner_identity()[k] for k in ("commit", "implementation_digest")}))).fetchone()
    brief_id, manifest_id, state = tuple(row.values()) if isinstance(row, dict) else tuple(row)
    if manifest_id != payload["manifest"]["manifest_id"]:
        raise BriefRefused("manifest_changed", f"the database attested manifest {manifest_id}, the brief was built for "
                           f"{payload['manifest']['manifest_id']}")
    return {"brief_id": brief_id, "manifest_id": manifest_id, "state_digest": state}


def persisted_brief_problem(conn, chart_id: str, generation: str, manifest_id: str, digest: str) -> str | None:
    """None when `digest` is the CURRENT verifier-persisted brief of the generation for this manifest and the generation's state is the
    one it was produced for; otherwise the named reason (`receipt_brief_not_persisted` / `_superseded` / `_state_changed`). The same
    database function the receipt's commit-time trigger calls."""
    row = conn.execute("SELECT public.ka_gochara_seal_brief_problem(%s::uuid, %s, %s::uuid, %s)",
                       (chart_id, generation, manifest_id, digest)).fetchone()
    return next(iter(row.values())) if isinstance(row, dict) else row[0]


def vj_lock(conn, chart_id: str) -> None:
    from .verification_job import take_locks
    take_locks(conn, chart_id)


def recompute_under_locks(conn, chart_id: str, generation: str, approved_digest: str, *, sealing_commit: str | None = None) -> dict:
    """The SEALING step's check, called inside the publishing transaction: take the seal locks (chart, then global), rebuild the
    payload with THE SAME code, and refuse (ApprovalMismatch) unless its sha256 is exactly the approved digest AND the candidate
    is still approvable. Call it BEFORE publishing — the manifest is a candidate in the approved payload."""
    if not isinstance(approved_digest, str) or not _DIGEST.match(approved_digest):
        raise ApprovalMismatch(f"the approved digest {approved_digest!r} is not a sha256")
    vj_lock(conn, chart_id)
    payload = build_payload(conn, chart_id, generation, sealing_commit=sealing_commit)
    got = payload_digest(payload)
    if got != approved_digest:
        raise ApprovalMismatch(f"the candidate is not what was approved: its approval payload now hashes to {got}, the "
                               f"approved brief digest is {approved_digest} — a changed candidate invalidates the approval")
    problems = _current_and_complete(payload)
    if problems:
        raise ApprovalMismatch("the approved candidate is no longer approvable: " + "; ".join(problems))
    return payload


__all__ = ["ApprovalMismatch", "BriefRefused", "LEDGER_MIGRATIONS", "OUTPUT_TABLES", "SCHEMA", "brief", "build_payload",
           "generation_output_identity", "payload_digest", "recompute_under_locks"]
