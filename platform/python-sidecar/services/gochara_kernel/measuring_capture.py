"""MB-3 stored-column export. No builder imports, database writes or acceptance.

The caller owns a REPEATABLE READ / SERIALIZABLE, READ ONLY transaction.
The export records observations; independent review and the sitting-log commit
binding are separate prerequisites to teardown. Never a 4.1 scoring artifact.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
from uuid import UUID

from . import measuring_report as mr

FILES = frozenset({"contacts.jsonl", "records.jsonl", "windows.jsonl", "horizon_basis.json",
                   "stretch_sink.jsonl", "digests.json"})
KEY_FIELDS = ("event_class", "affected_person", "agent", "relation", "object_id", "object_role",
              "contact_id", "path_id", "rule_version", "prerequisites", "source_text")


class CaptureRefused(ValueError):
    """A named incomplete or inconsistent capture, never a successful receipt."""


def _plain(value):
    if isinstance(value, datetime):
        if value.utcoffset() is None:
            raise CaptureRefused("naive_datetime")
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    # psycopg Range. Empty, infinite or non-half-open support must not silently
    # become an apparently ordinary interval in a golden or ratio.
    if hasattr(value, "bounds") and hasattr(value, "lower"):
        if value.isempty or value.bounds != "[)" or value.lower is None or value.upper is None:
            raise CaptureRefused("support_interval_unbounded_or_not_half_open")
        return [_plain(value.lower), _plain(value.upper)]
    return value


def canonical(value):
    return json.dumps(_plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _digest(value):
    return sha256(canonical(value).encode("utf-8")).hexdigest()


def golden_record(row):
    """Recreate MB-3.2 from stored columns and ordered prerequisite rows only.

    Frame and optional P1 anchors follow the published natural-key definition
    (evaluator.py:137–157), implemented independently rather than imported.
    """
    required = set(KEY_FIELDS) | {"frame_kind", "frame_arg", "record_id", "admission_state",
                                  "operator_role", "temporal_support_intervals",
                                  "period_anchor_lord", "period_anchor_level"}
    if not required <= row.keys():
        raise CaptureRefused("stored_record_missing: " + ",".join(sorted(required - row.keys())))
    key = {field: row[field] for field in KEY_FIELDS}
    key["frame"] = row["frame_kind"] if row["frame_arg"] is None else f"{row['frame_kind']}:{row['frame_arg']}"
    if row["period_anchor_lord"] is not None:
        key.update(period_anchor_lord=row["period_anchor_lord"], period_anchor_level=row["period_anchor_level"])
    gkey = canonical(key)
    return {"gkey": gkey, "gkey_sha256": sha256(gkey.encode("utf-8")).hexdigest(),
            "record_id": str(row["record_id"]), "admission_state": row["admission_state"],
            "operator_role": row["operator_role"], "supports": _plain(row["temporal_support_intervals"])}


def _sorted(rows):
    return sorted((_plain(r) for r in rows), key=canonical)


def make_bundle(*, binding, contacts, records, windows, horizon_basis, stretch_sink, informational):
    """Pure assembly; ordering independent, multiplicity retained, no timestamps."""
    fields = {"chart_id", "generation", "run_id", "manifest_id", "source_commit"}
    if not fields <= binding.keys() or any(not isinstance(binding[k], str) or not binding[k] for k in fields):
        raise CaptureRefused("capture_binding_missing")
    if re.fullmatch(r"[0-9a-f]{40}", binding["source_commit"]) is None:
        raise CaptureRefused("capture_source_commit_invalid")
    contacts, records, windows = _sorted(contacts), _sorted(golden_record(r) for r in records), _sorted(windows)
    groups = defaultdict(list)
    for r in records:
        key = json.loads(r["gkey"])
        groups[(key["event_class"], key["path_id"])].append(r)
    record_digests = []
    for (cls, path), rows in sorted(groups.items()):
        # gkey hashes alone cannot detect a support/admission/role regression.
        payloads = _sorted({k: v for k, v in r.items() if k != "record_id"} for r in rows)
        record_digests.append({"event_class": cls, "path_id": path, "count": len(rows),
                               "gkeys_sha256": _digest(sorted(r["gkey_sha256"] for r in rows)),
                               "payload_sha256": _digest(payloads)})
    obligations = defaultdict(list)
    for c in contacts:
        obligations[(c["body"], c["relation_kind"], c["canonical_target"])].append(c)
    contact_digests = [{"body": body, "relation": relation, "canonical_target": target,
                        "count": len(rows), "sha256": _digest(rows)}
                       for (body, relation, target), rows in sorted(obligations.items())]
    return {"contacts.jsonl": contacts, "records.jsonl": records, "windows.jsonl": windows,
            "horizon_basis.json": _plain(horizon_basis), "stretch_sink.jsonl": _sorted(stretch_sink),
            "digests.json": {"schema": "ky.measuring_golden/1", "binding": dict(binding),
                             "records": record_digests, "contacts": contact_digests,
                             "windows_sha256": _digest(windows), "informational": _plain(informational),
                             "acceptance": None, "source_commit_attested": None}}


def write_bundle(destination, bundle):
    """Create once. An interrupted export has no valid MANIFEST and cannot pass."""
    if set(bundle) != FILES:
        raise CaptureRefused("golden_file_set")
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name in sorted(FILES):
        value = bundle[name]
        text = ("".join(canonical(row) + "\n" for row in value) if name.endswith(".jsonl")
                else canonical(value) + "\n")
        data = text.encode("utf-8")
        (destination / name).write_bytes(data)
        hashes[name] = sha256(data).hexdigest()
    manifest = "".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items()))
    (destination / "MANIFEST.sha256").write_text(manifest, encoding="utf-8")
    return verify_bundle(destination)


def verify_bundle(directory):
    """Exact file set, canonical whole manifest, every file digest, no symlinks."""
    directory = Path(directory)
    if not directory.is_dir():
        raise CaptureRefused("golden_missing")
    if {p.name for p in directory.iterdir()} != FILES | {"MANIFEST.sha256"}:
        raise CaptureRefused("golden_file_set")
    if any(p.is_symlink() or not p.is_file() for p in directory.iterdir()):
        raise CaptureRefused("golden_file_set")
    raw = (directory / "MANIFEST.sha256").read_bytes()
    try:
        lines = raw.decode("utf-8").splitlines(keepends=True)
        entries = [re.fullmatch(r"([0-9a-f]{64})  ([a-z_]+\.jsonl?)\n", line) for line in lines]
        if (len(lines) != len(FILES) or any(e is None for e in entries)
                or [e[2] for e in entries] != sorted(FILES)):
            raise ValueError
    except (UnicodeError, ValueError):
        raise CaptureRefused("golden_manifest_invalid") from None
    for entry in entries:
        if sha256((directory / entry[2]).read_bytes()).hexdigest() != entry[1]:
            raise CaptureRefused(f"golden_digest_mismatch: {entry[2]}")
    return {"schema": "ky.measuring_golden_receipt/1", "manifest_sha256": sha256(raw).hexdigest(),
            "files": {e[2]: e[1] for e in entries}, "acceptance": None}


def _rows(conn, sql, params):
    cur = conn.execute(sql, params)
    return [dict(zip((c.name for c in cur.description), row)) for row in cur.fetchall()]


def validate_candidate_manifest(manifest):
    """Stamp/scope syntax only. No steward stamp proof or basis re-derivation."""
    vector = manifest["input_generation_vector"]
    if isinstance(vector, str):
        vector = json.loads(vector)
    if not isinstance(vector, dict):
        raise CaptureRefused("measuring_manifest_invalid")
    marker = vector.get("test_slice")
    if manifest["status"] != "candidate":
        raise CaptureRefused("measuring_build_not_candidate")
    if (vector.get("stored_scope") != "test_slice" or not isinstance(marker, dict)
            or marker.get("run") != "all_classes_full"):
        raise CaptureRefused("measuring_scope_not_all_classes_full")
    if (marker.get("schema") != mr.MARKER_SCHEMA or not isinstance(marker.get("marker_digest"), str)
            or re.fullmatch(r"[0-9a-f]{64}", marker["marker_digest"]) is None
            or not isinstance(marker.get("horizon"), list) or len(marker["horizon"]) != 2
            or not isinstance(marker.get("classes"), list)):
        raise CaptureRefused("marker_incomplete")
    if (any(not isinstance(c, str) for c in marker["classes"])
            or len(marker["classes"]) != len(mr.SCORED_CLASSES) or set(marker["classes"]) != mr.SCORED_CLASSES):
        raise CaptureRefused("class_census_mismatch")
    try:
        horizon = tuple(mr.as_utc_date(t) for t in (manifest["lo"], manifest["hi"]))
        if horizon != mr.RULED_MEASURING_HORIZON:
            raise CaptureRefused("horizon_mismatch")
        if tuple(mr.as_utc_date(t) for t in marker["horizon"]) != horizon:
            raise CaptureRefused("marker_horizon_mismatch")
    except mr.MeasuringReportError as exc:
        raise CaptureRefused(str(exc)) from exc
    basis = vector.get("horizon_basis")
    if not isinstance(basis, dict) or not basis:
        raise CaptureRefused("horizon_basis_missing")
    return vector


def read_candidate(conn, *, chart_id, generation, run_id, source_commit, stretch_sink):
    """Read one snapshot. Caller supplies exported log records and source claim.

    The caller's run ID and declared commit are recorded, not independently
    attested. Runtime/log and sink verification belong to verifier B, not this
    exporter. All candidate-table reads are chart AND generation scoped.
    """
    from psycopg.pq import TransactionStatus

    if conn.info.transaction_status != TransactionStatus.INTRANS:
        raise CaptureRefused("capture_requires_read_only_snapshot")
    readonly = conn.execute("SHOW transaction_read_only").fetchone()[0]
    isolation = conn.execute("SHOW transaction_isolation").fetchone()[0]
    if readonly != "on" or isolation not in ("repeatable read", "serializable"):
        raise CaptureRefused("capture_requires_read_only_snapshot")
    pair = (chart_id, generation)
    manifests = _rows(conn, "SELECT manifest_id, status, input_generation_vector, lower(horizon) AS lo, upper(horizon) AS hi"
                      " FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s", pair)
    if len(manifests) != 1:
        raise CaptureRefused("measuring_manifest_missing" if not manifests else "measuring_manifest_ambiguous")
    manifest = manifests[0]
    vector = validate_candidate_manifest(manifest)
    if conn.execute("SELECT count(*) FROM public.ka_gochara_generation_seal WHERE chart_id = %s AND generation = %s", pair).fetchone()[0]:
        raise CaptureRefused("measuring_build_sealed")
    if conn.execute("SELECT count(*) FROM public.kala_gochara_authority WHERE chart_id = %s AND authoritative_generation = %s", pair).fetchone()[0]:
        raise CaptureRefused("measuring_build_published")
    basis = vector["horizon_basis"]
    contacts = _rows(conn, "SELECT c.contact_id, c.body, c.relation_kind, o.canonical_target, c.t_in, c.t_out, c.t_exact, c.delta_lambda"
                     " FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
                     " ON o.physical_object_id = c.physical_object_id WHERE c.chart_id = %s AND c.generation = %s", pair)
    records = _rows(conn, "SELECT r.*, COALESCE((SELECT jsonb_agg(jsonb_build_array(p.predicate_id, p.predicate_rule_version) ORDER BY p.ordinal)"
                    " FROM public.ka_gochara_record_prerequisite p WHERE p.record_id = r.record_id"
                    " AND p.chart_id = r.chart_id AND p.generation = r.generation), '[]'::jsonb) AS prerequisites"
                    " FROM public.ka_gochara_relationship_record r WHERE r.chart_id = %s AND r.generation = %s", pair)
    windows = _rows(conn, "SELECT event_class, path_id, rule_version, lower(interval) AS lo, upper(interval) AS hi"
                    " FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s", pair)
    return make_bundle(binding={"chart_id": str(chart_id), "generation": generation, "run_id": run_id,
                                "manifest_id": str(manifest["manifest_id"]), "source_commit": source_commit},
                       contacts=contacts, records=records, windows=windows, horizon_basis=basis, stretch_sink=stretch_sink,
                       informational={"input_vector": vector, "horizon": [manifest["lo"], manifest["hi"]],
                                      "candidate_status": manifest["status"]})
