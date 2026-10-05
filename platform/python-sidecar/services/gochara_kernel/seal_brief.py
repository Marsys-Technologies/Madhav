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
LEDGER_MIGRATIONS = ("1204", "1206", "1232", "1233", "1240", "1241", "1305")
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


def canonical_json(v, _path: str = "$") -> str:
    """The STRICT canonical JSON of the approval payload and everything displayed with it (F-R13-6): sorted keys (code point), no
    whitespace, UTF-8 unescaped — and EVERY type is encoded by an explicit rule or REFUSED, so a digest (or a displayed brief) can never
    depend on `str()` of something unforeseen. Rules: None/bool/int/str as JSON; Decimal (finite only) as a plain-notation JSON number;
    UUID as its lowercase hyphenated string; an aware datetime as UTC ISO-8601 with microseconds and `Z` (a naive one is refused); a
    date as ISO-8601; dict (string keys only) and list/tuple recursively. float, bytes, set, NaN/Infinity, naive datetimes, non-string
    keys and anything else raise `NotCanonicallyEncodable` naming the path. For the types the payload actually carries the output is
    byte-identical to `window_gate._canon` (the form every existing digest was computed in)."""
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
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, _uuid.UUID):
        return json.dumps(str(v), ensure_ascii=False)
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
        return "{" + ",".join(json.dumps(k, ensure_ascii=False) + ":" + canonical_json(v[k], f"{_path}.{k}") for k in sorted(v)) + "}"
    if isinstance(v, (list, tuple)):
        return "[" + ",".join(canonical_json(x, f"{_path}[{i}]") for i, x in enumerate(v)) + "]"
    raise NotCanonicallyEncodable(f"{_path}: {type(v).__name__} has no canonical JSON rule (floats, bytes, sets and unknown types are refused)")


_canon = canonical_json


def payload_digest(payload: dict) -> str:
    return hashlib.sha256(_canon(payload).encode("utf-8")).hexdigest()


# ── transport of the DISPLAY brief (F-R13-2) ─────────────────────────────────────────────────────────────────────
# The full brief grows with the number of event classes (~9.5 KB per class + ~8 KB fixed; ~255 KB at 26 classes — at the size of a CI log
# entry limit), so the job's stdout is a COMPACT line and the brief travels another way. In every route the bytes are the canonical JSON of
# the payload, so `sha256(bytes) == the persisted brief digest` is directly checkable by the reader.
CHUNK_RAW_BYTES = 48 * 1024
#: the version of the stdout contract, carried by the compact line as `contract_version` (ST-TRANSPORT-2); the chunk lines are bound to the compact line
#: by their `sha256` and carry no version of their own
TRANSPORT_CONTRACT = "seal_brief_transport/1"


def brief_bytes(result: dict) -> bytes:
    """The canonical bytes of the brief — refusing (BriefRefused) if they do not hash to the digest the result carries."""
    raw = _canon(result["payload"]).encode("utf-8")
    if hashlib.sha256(raw).hexdigest() != result["sha256"]:
        raise BriefRefused("brief_bytes_digest_mismatch", "the brief's canonical bytes do not hash to its digest")
    return raw


def brief_chunk_lines(raw: bytes, digest: str, chunk_bytes: int = CHUNK_RAW_BYTES) -> list[str]:
    """The chunked-lines transport: `{"b64": <base64 of the i-th slice>, "brief_chunk": i, "of": n, "sha256": <whole-brief digest>}`, one
    canonical-JSON line each; concatenating the decoded slices in index order gives the brief bytes."""
    import base64
    if chunk_bytes < 1:
        raise ValueError("chunk_bytes must be positive")
    parts = [raw[i:i + chunk_bytes] for i in range(0, len(raw), chunk_bytes)] or [b""]
    return [_canon({"brief_chunk": i, "of": len(parts), "sha256": digest, "b64": base64.b64encode(p).decode("ascii")})
            for i, p in enumerate(parts)]


def reassemble_chunks(lines: list[str]) -> bytes:
    """The reader's side of the chunked transport: refuses a missing/duplicated/foreign chunk and a whole that does not hash to the digest."""
    import base64
    docs = [json.loads(x) for x in lines]
    if not docs:
        raise BriefRefused("no_chunks", "no brief chunk lines")
    total, digest = docs[0]["of"], docs[0]["sha256"]
    if sorted(d["brief_chunk"] for d in docs) != list(range(total)) or any(d["of"] != total or d["sha256"] != digest for d in docs):
        raise BriefRefused("chunks_incomplete", "the brief chunks are missing, duplicated or from different briefs")
    raw = b"".join(base64.b64decode(d["b64"]) for d in sorted(docs, key=lambda d: d["brief_chunk"]))
    if hashlib.sha256(raw).hexdigest() != digest:
        raise BriefRefused("chunks_digest_mismatch", "the reassembled brief does not hash to its digest")
    return raw


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
    # G12 (Codex round 1, finding 6): a FIRST seal requires the snapshot's COPY of the L1 inputs (migration 1305). A legacy snapshot points at rows an L1 rebuild
    # re-issues, so a generation sealed on it could never be re-verified; the replay of an ALREADY sealed generation is unaffected.
    from .inventory_verifier import snapshot_copies
    copies = snapshot_copies(conn, chart_id, generation)
    already_sealed = bool(_rows(conn, "SELECT 1 FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s", (chart_id, generation)))
    if copies is not None and copies["facts"] is None and not already_sealed:
        raise BriefRefused("snapshot_without_copy", "the search-input snapshot is the LEGACY shape (ids only, no copy of the L1 rows it consumed): apply "
                           "migration 1305 and rebuild; a first seal needs a self-contained snapshot (an L1 rebuild would otherwise leave it unverifiable)")
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
    natal_tiers = natal_input_tiers(conn, chart_id, generation)     # ONE read feeds both the disclosure and the observed-tiers field (F-R16-6)
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
                        "ephemeris_binding": EPHEMERIS_BINDING_DISCLOSURE,
                        "natal_inputs": natal_disclosure(natal_tiers),
                        "natal_input_tiers": natal_tiers,
                        "named_limits": __import__("services.gochara_kernel.scope_response", fromlist=["x"]).named_limits(),
                        "attestation_binding": "composition: inputs/2 per grain + DB-guarded path pins + the 1206 inventory "
                                               "verification row + the generation-wide output identity above",
                        "candidate_adapter": "three published-only completeness arms are re-derived against the candidate "
                                             "manifest; the authoritative gate is the seal's, on the published row"},
        "seal_is_not_a_flip": SEAL_IS_NOT_A_FLIP,
    }


ALL_NULL_POLICY = "all_null_candidate/1"
#: R15-6 (ii): what binds the ephemeris, said plainly — the sealing job cannot re-derive it
EPHEMERIS_BINDING_DISCLOSURE = (
    "The ephemeris identity (the .se1 files opened, the Swiss library and platform, the probe digest) is bound in the manifest's input vector and "
    "re-verified by the verifier job before this brief; the sealing job holds no ephemeris corpus and does NOT re-derive it at seal. It stays bound "
    "through the verifier's producer image digest recorded with this brief (`producer.image_digest`), and the interval from final verification to "
    "seal commit is covered by a written freeze and identity-readback procedure outside the database, not by a seal-time check.")
NATAL_SUBJECTS = ("LAGNA", "SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT", "RAH_MEAN", "KET_MEAN")
#: VERBATIM (steward ruling, F-R15-4) — printed ONLY when the consumed natal rows are exactly the ten subjects and every one is at tier `single`
NATAL_SINGLE_TIER_DISCLOSURE = (
    "The ten natal longitudes this generation consumes (LAGNA, SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN, KET_MEAN; chart_facts "
    "graha_position longitude_sidereal, lahiri_chitrapaksha) are read at the tier they carry, which is `single` (one derivation, no independent second "
    "pass); they are bound by content digest, not verified by this generation.")


def natal_input_tiers(conn, chart_id: str, generation: str) -> dict[str, list[str]]:
    """{subject: sorted distinct verification_pass_status} of the L1 rows the generation's search-input snapshot CONSUMED — read, never assumed.
    From the snapshot's own COPY (metadata block) when it has one (G12): the tier the rows carried WHEN CONSUMED, not whatever live L1 says today."""
    out: dict[str, set[str]] = {}
    from .inventory_verifier import snapshot_copies
    copies = snapshot_copies(conn, chart_id, generation)
    if copies is not None and copies["facts"] is not None:
        for e in copies["facts"]:
            out.setdefault(str(e["content"]["fact_subject"]), set()).add(str(e["metadata"]["verification_pass_status"]))
        return {k: sorted(v) for k, v in sorted(out.items())}
    for subject, tier in _rows(
            conn, "SELECT f.fact_subject, f.verification_pass_status FROM public.chart_facts f"
                  " JOIN public.ka_gochara_search_input_snapshot s ON s.chart_id = f.chart_id AND f.fact_id = ANY (s.consumed_fact_ids)"
                  " WHERE s.chart_id = %s AND s.generation = %s", (chart_id, generation)):
        out.setdefault(str(subject), set()).add(str(tier))
    return {k: sorted(v) for k, v in sorted(out.items())}


def natal_disclosure(tiers: dict[str, list[str]]) -> str:
    """The single-tier sentence, but only while it is TRUE of the rows actually consumed; otherwise the OBSERVED tiers are printed instead, so
    the disclosure cannot go stale (F-R15-4)."""
    from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT
    if set(tiers) == set(NATAL_SUBJECTS) and all(t == [UNVERIFIED_DEFAULT] for t in tiers.values()):
        return NATAL_SINGLE_TIER_DISCLOSURE
    seen = "; ".join(f"{k}={'/'.join(v)}" for k, v in tiers.items()) or "no consumed natal row was found"
    return ("The natal longitudes this generation consumes (chart_facts graha_position longitude_sidereal, lahiri_chitrapaksha) are read at the tiers they "
            f"carry — observed: {seen} — and are NOT all at the single tier the standard disclosure states; they are bound by content digest, "
            "not verified by this generation.")


#: VERBATIM the packet's §R13b sentence (F-R14-1; steward ruling) — it is inside the digest preimage, so it must be exactly the sentence the
#: packet, §R12a and the runbook promise. It makes NO claim about the database's contents at every moment: the gate enforces it at seal.
ALL_NULL_DISCLOSURE = (
    "The result policy `all_null_candidate/1` forbids any numerical result or qualified valence in every record, window and window-membership "
    "link of this generation, and the gate refuses legacy projection rows for it (`record_result_not_policy`, `legacy_projection_rows_present`); "
    "this is a property the gate enforces at seal, not a property of the database's contents at every moment.")


def _policy_disclosure(policy: str) -> str:
    """The disclosure's wording follows the MANIFEST's policy name — it never asserts the all-NULL claim for a manifest that selects
    another policy (F-R13 / Stream B): the all-NULL sentence is said only under `all_null_candidate/1`, and even there only as what the gate
    ENFORCES AT SEAL (F-R14-1) — never as a claim about the database's contents at every moment."""
    if policy == ALL_NULL_POLICY:
        return ALL_NULL_DISCLOSURE
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


ENV_IMAGE_DIGEST = "GOCHARA_RUNNER_IMAGE_DIGEST"      # set by the job DEFINITION to the immutable image digest (sha256:<64 hex>)
ENV_EXECUTION = "CLOUD_RUN_EXECUTION"                   # set by Cloud Run itself for every job execution
_IMAGE_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}\Z")


def producer_identity(environ=None) -> dict:
    """WHO is producing this brief (R13-3), from the running job's own environment: the commit of the code (`GOCHARA_RUNNER_COMMIT`, else the
    repository HEAD), the immutable image digest (`GOCHARA_RUNNER_IMAGE_DIGEST`) and the Cloud Run execution (`CLOUD_RUN_EXECUTION`). An
    absent or malformed one REFUSES — a brief of unknown producer is not an approval basis."""
    import os
    from . import window_gate as wg
    env = os.environ if environ is None else environ
    commit = env.get(wg.ENV_RUNNER_COMMIT) or wg._git_head()
    image, execution = env.get(ENV_IMAGE_DIGEST), env.get(ENV_EXECUTION)
    problems = []
    if not commit or not str(commit).strip():
        problems.append(f"the producing code's commit cannot be named ({wg.ENV_RUNNER_COMMIT} unset, no repository HEAD)")
    if not isinstance(image, str) or not _IMAGE_DIGEST.match(image):
        problems.append(f"{ENV_IMAGE_DIGEST} is absent or not 'sha256:<64 hex>' (the job definition must pin the immutable image)")
    if not isinstance(execution, str) or not execution.strip():
        problems.append(f"{ENV_EXECUTION} is absent (the brief must name the execution that produced it)")
    if problems:
        raise BriefRefused("producer_identity_absent", "; ".join(problems))
    return {"commit": str(commit).strip(), "image_digest": image, "execution_id": execution.strip()}


def persist_brief(conn, result: dict, *, producer: dict | None = None) -> dict:
    """F-R12-4 / R13-3: persist the brief the VERIFIER just produced (`brief()`'s result) in `ka_gochara_seal_brief`, inside the same
    transaction that holds the seal locks, with its producer identity (`producer_identity()` unless one is supplied: commit, image digest,
    execution id). The database attests the manifest, the state digest, the session login and the time (whatever this INSERT carries for
    them is overwritten) and takes the seal locks itself. The producing commit must be the sealing commit the payload names. Returns
    `{brief_id, manifest_id, state_digest}`; the producer travels beside it (`producer` key of the compact line)."""
    from . import window_gate as wg
    payload = result["payload"]
    prod = producer if producer is not None else producer_identity()
    sealing = payload["code"].get("sealing_commit")
    if sealing is not None and prod["commit"] != sealing:
        raise BriefRefused("producer_not_sealing_commit", f"the brief was produced by commit {prod['commit']}, the sealing commit it names is "
                           f"{sealing} — only code at the sealing commit may brief it")
    row = conn.execute(
        "INSERT INTO public.ka_gochara_seal_brief (chart_id, generation, manifest_id, brief_digest, state_digest, runner_identity,"
        " producer_commit, image_digest, execution_id)"
        " VALUES (%s::uuid, %s, %s::uuid, %s, repeat('0', 64), %s::jsonb, %s, %s, %s) RETURNING brief_id, manifest_id::text, state_digest",
        (payload["chart_id"], payload["generation"], payload["manifest"]["manifest_id"], result["sha256"],
         _canon({k: wg.runner_identity()[k] for k in ("commit", "implementation_digest")}),
         prod["commit"], prod["image_digest"], prod["execution_id"])).fetchone()
    brief_id, manifest_id, state = tuple(row.values()) if isinstance(row, dict) else tuple(row)
    if manifest_id != payload["manifest"]["manifest_id"]:
        raise BriefRefused("manifest_changed", f"the database attested manifest {manifest_id}, the brief was built for "
                           f"{payload['manifest']['manifest_id']}")
    return {"brief_id": brief_id, "manifest_id": manifest_id, "state_digest": state}


def persisted_brief_problem(conn, chart_id: str, generation: str, manifest_id: str, digest: str, *, brief_id: int | None = None,
                            sealing_commit: str | None = None, execution_id: str | None = None) -> str | None:
    """None when `digest` is the CURRENT verifier-persisted brief of the generation for this manifest, written by the verifier login, in
    the generation's state, and — when given — it is THAT brief id, produced by that commit in that execution; otherwise the named reason
    (`receipt_brief_not_persisted` / `_superseded` / `_not_from_verifier` / `_state_changed` / `receipt_brief_id_mismatch` /
    `receipt_brief_producer_commit_mismatch` / `receipt_brief_execution_mismatch`). The same checks the receipt's commit-time trigger runs."""
    row = conn.execute("SELECT public.ka_gochara_seal_brief_problem(%s::uuid, %s, %s::uuid, %s)",
                       (chart_id, generation, manifest_id, digest)).fetchone()
    why = next(iter(row.values())) if isinstance(row, dict) else row[0]
    if why:
        return why
    cur = conn.execute("SELECT brief_id, producer_commit, execution_id FROM public.ka_gochara_seal_brief"
                       " WHERE chart_id = %s::uuid AND generation = %s ORDER BY brief_id DESC LIMIT 1", (chart_id, generation)).fetchone()
    cur_id, cur_commit, cur_exec = tuple(cur.values()) if isinstance(cur, dict) else tuple(cur)
    if brief_id is not None and cur_id != brief_id:
        return "receipt_brief_id_mismatch"
    if sealing_commit is not None and cur_commit != sealing_commit:
        return "receipt_brief_producer_commit_mismatch"
    if execution_id is not None and cur_exec != execution_id:
        return "receipt_brief_execution_mismatch"
    return None


#: bounded waits (steward ruling M20261002T175331): a stuck lock or a runaway statement must end in a NAMED refusal with nothing written, never
#: hang. Applied transaction-locally (`set_config(..., true)`), so they end with the transaction. The 15-minute statement bound is ~25x an
#: ESTIMATE of the worst case (26 classes x 50 synthetic, ~35 s extrapolated from measured read costs) — not a measured seal at real volumes.
SEAL_STATEMENT_TIMEOUT = "15min"
SEAL_LOCK_TIMEOUT = "2min"
BRIEF_LOCK_TIMEOUT = "2min"


SEAL_IDLE_IN_TRANSACTION_TIMEOUT = "10min"   # (R15) the server ends a sealing session that holds locks while doing nothing


def set_local_timeouts(conn, *, statement: str | None = None, lock: str | None = None, idle_in_transaction: str | None = None) -> None:
    """Transaction-local `statement_timeout` / `lock_timeout` / `idle_in_transaction_session_timeout` (call inside the transaction, before the
    first lock is taken)."""
    for name, value in (("statement_timeout", statement), ("lock_timeout", lock),
                        ("idle_in_transaction_session_timeout", idle_in_transaction)):
        if value is not None:
            conn.execute("SELECT set_config(%s, %s, true)", (name, value))


def registry_problem(conn, chart_id: str, generation: str) -> str | None:
    """R15-6 (i): re-derive the REGISTRY digest and census from the LIVE registry tables and compare them with the manifest vector's. None when
    they agree; else the named difference. Reads `ka_gochara_rule_path`, `_rule_path_prerequisite`, `_rule_path_soft_factor`,
    `ka_gochara_predicate`, `ka_gochara_factor` and `ka_gochara_rule_path_seal` (SELECT only) with the SAME function the build used, under the
    seal locks the caller holds."""
    import json
    from decimal import Decimal
    from . import input_vector as iv
    from . import rule_registry as rr
    row = _rows(conn, "SELECT input_generation_vector::text FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                (chart_id, generation))
    if not row:
        return "no manifest"
    stored = json.loads(row[0][0], parse_float=Decimal).get("registry") or {}
    payload = iv.registry_payload(conn, rr.bound_path_refs())
    live = {"digest": iv.registry_digest_of(payload), "census": sorted([list(c) for c in payload["census"]])}
    out = []
    if live["digest"] != stored.get("digest"):
        out.append(f"registry digest: manifest {stored.get('digest')}, live {live['digest']}")
    if live["census"] != sorted(stored.get("census") or []):
        out.append("registry census (the sealed (path, version) set) differs from the manifest's")
    return "; ".join(out) or None


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
