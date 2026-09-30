#!/usr/bin/env python3
"""step06_candidate_build.py — WP10 runbook step 6 (plan §9): '4.0' candidate build.

Drives the ledger lifecycle for the candidate generation on ONE chart:
register_convention → publish_candidate (input generation vector recorded) →
write_contacts + write_coverage. '3.0' is never touched; the authority stays
'3.0' until step 8.

Tranche 2 (PRODUCTION_TRANCHE_2_AUTHORIZED). Sheet A-3.

Flags (remainder brief §7.A: "all §4 flags on", recorded in the input
generation vector):
    activity_shape=linear_no_box  orb_max_deg=--orb-deg (M-1 fallback 5.0°,
        since WP8 M-1's 1.0° recommendation is NOT ratified; 7.C allows the
        declared fallback)
    moon_channel=separate  nodal_drishti=removed  sade_sati_mode=testimony
    kakshya_bindu_interim=true
plus N-17/N-22 and M-8's rows as recorded vector entries.

Episodes: at tranche time the kernel pipeline enumerates them; this script
consumes that enumeration as `--episodes-json` (a list of episode dicts in the
ledger's `_normalize_episode` shape, exactly what write_contacts accepts) and
`--coverage-json` (a list of coverage partition dicts). For rehearsal,
`--rehearse-synthetic` fabricates a small synthetic episode set instead —
synthetic data only, never pointed at a real chart.

NDJSON stream input (Pravāha A2.5, CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §2):
`--episodes-ndjson <path-or-glob>` (local rehearsal) or `--input-manifest
<manifest.json>` (the finalized century chain — the only shape century_run.py
drives) reads the per-body NDJSON objects step06_enumerate_episodes.py wrote
(one episode object per line). Both are mutually exclusive with
--episodes-json.

Bounded memory end-to-end (ASTRA A2.5 review amendment 1): the read is a
STREAMED k-way merge over the per-body objects — local files or gs:// URIs
(google-cloud-storage blob streaming, lazy import; injectable transport for
tests) — and the insert is bounded: ledger.write_contacts_streaming
normalizes and inserts in fixed-size batches inside the ONE candidate
transaction. Neither the episode dicts nor the normalized rows nor a
contact-id list are ever materialized century-scale in this process.

Canonical stream order (amendment 6 — the equivalence definition): each
per-body object is written sorted by the TOTAL order `episode_stream_key` =
(t_in, body, relation, canonical-json of the episode); the merge preserves it
and VERIFIES it per object (an unsorted object — foreign, hand-made, or
stale-format — is rejected, never silently re-ordered). Equivalence with the
monolithic --episodes-json build is defined precisely as: (a) the same
contact row SET keyed by the pinned §3.2 contact_id (dedupe/identity), (b)
the same coverage row set with insertion order by partition_key (the order
build_coverage_rows emits monolithically), and (c) the same manifest
content_digest once volatile metadata (computed_at, build_id, manifest
linkage) is controlled — the digest itself (ledger._canonical_row_set) is
order-independent over the canonically sorted DB row set.

Finalized input manifest (amendment 2, §N.8): with --input-manifest the build
verifies — before any candidate success (commit/GREEN) — the manifest's run
identity (run_id uniform across manifest and every object), chart_id,
generation, horizon, the full expected body set (PERSISTED_BODIES, imported,
never restated), the coverage binding (order-independent sha256 of the merged
coverage rows), and every object's streamed line count, byte count, and
sha256. A missing, truncated (clean-prefix truncations included), altered,
mixed-run, or unreadable object FAILS the build (exit 3, transaction rolled
back) — a truncated or partial stream can never earn GREEN/COMPLETE.

The factor-level delta report vs '3.0' (§4.11, WP8's
WP8_FACTOR_DELTA_REPORT_v1_0.md artifact) is attached to the manifest via
--delta-report; at tranche time it is REQUIRED (7.C), in rehearsal optional.

Usage:
    python3 step06_candidate_build.py --dsn postgresql://... --chart-id <uuid> \
        [--horizon-start 2020-01-01 --horizon-end 2030-01-01] \
        [--episodes-json eps.json | --episodes-ndjson 'eps/*.ndjson'] \
        --coverage-json cov.json (or --rehearse-synthetic) \
        [--orb-deg 5.0] [--delta-report path] [--evidence]

Exit codes: 0 built; 3 cannot proceed; 4 production refusal; 6 publish refused
(published generation — a rebuild after publication is a NEW label, plan §4.7);
7 refused: the chart's house_vedha or mūrti rows are not FRESH against bg_transit_rules /
bg_vedha_malefic_scale / bg_transit_moorti (§12.9 — a candidate must not be built on rows carrying
refuted citations). Skipped, and recorded as NOT_RUN, under --rehearse-synthetic.
"""
from __future__ import annotations

import glob
import hashlib
import heapq
import importlib.util
import io
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, redact_text, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]
_LEDGER_PATH = SIDECAR / "services" / "gochara_kernel" / "ledger.py"

UTC = timezone.utc

# The candidate's input generation vector (7.C: each flag recorded). This is
# the DECLARED vector; the build records it verbatim on the manifest.
GENERATION_VECTOR_FLAGS = {
    "activity_shape": "linear_no_box",
    "moon_channel": "separate",
    "nodal_drishti": "removed",        # N-14
    "sade_sati_mode": "testimony",     # N-15
    "kakshya_bindu_interim": True,     # N-22
    "overlay_stamps": True,            # N-17 (three-consumer stamps populated)
    "vedha_exceptions": "m8_rows",     # M-8's ruled rows
}

CONVENTION_VECTOR = {
    "zodiac": "sidereal",
    "ayanamsha": "lahiri_chitrapaksha",
    "sidereal_method": "swe_flg_sidereal",
    "node_model": "mean",
    "node_source": "swiss_mean_node_flg_sidereal",
    "epoch_convention": "noon_ut_knot_abscissa",
    "time_scale": "ut_to_tt_swe_deltat",
    "house_system": "whole_sign",
    "ephemeris_mode": "flg_swieph",
    "method_version": "1.0.0",
}


def _load_ledger():
    """Load ledger.py by file path (same discipline as test_wp6_ledger.py:
    the WP3a package __init__ is a sibling workstream's surface)."""
    spec = importlib.util.spec_from_file_location("cutover_step06_ledger", _LEDGER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _coerce_episode_times(episodes: list[dict]) -> list[dict]:
    """JSON carries instants as ISO strings; the ledger's contact-id path and
    the B1 naive-instant rejection both expect tz-aware datetimes. Parse
    t_in/t_exact/t_out when they arrive as strings (ISO with offset)."""
    for ep in episodes:
        for key in ("t_in", "t_exact", "t_out"):
            v = ep.get(key)
            if isinstance(v, str):
                ep[key] = datetime.fromisoformat(v)
    return episodes


def read_episodes_ndjson(path_or_glob: str) -> list[dict]:
    """Rehearsal-scale materializing read of concatenated per-body NDJSON
    (decade payloads, unit tests). The CENTURY build never uses this: it
    streams through EpisodeObjectStream + iter_episodes_merged into
    ledger.write_contacts_streaming (see the module docstring). Retained for
    small local payloads; sorts by the total canonical stream key, so the
    result is deterministic regardless of file/line order."""
    paths = sorted(glob.glob(path_or_glob))
    if not paths and Path(path_or_glob).exists():
        paths = [path_or_glob]
    if not paths:
        raise FileNotFoundError(
            f"--episodes-ndjson matched no files: {path_or_glob!r}")
    episodes: list[dict] = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    episodes.append(json.loads(line))
    _coerce_episode_times(episodes)
    episodes.sort(key=episode_stream_key)
    return episodes


# ── streamed century consumption (Pravāha A2.5; ASTRA review amendments 1/2/6) ─


class EpisodeStreamError(ValueError):
    """A stream object is unreadable, unparsable, or violates the canonical
    per-object ordering — the build fails, never a silent repair."""


class ManifestVerificationError(ValueError):
    """The finalized input manifest fails verification (§N.8): missing,
    truncated, altered, mixed-run, or non-final input can never earn
    GREEN/COMPLETE."""


def episode_stream_key(ep: dict) -> tuple:
    """The TOTAL canonical order for the streamed century build (amendment 6):
    (t_in, body, relation, canonical-json). The first three components are the
    dedupe_episodes sort key; because (t_in, body, relation) does not totally
    order distinct contacts, the canonical JSON serialization is the
    deterministic tie-break — two distinct episodes never compare equal, so
    the merged order is independent of shard/ingestion order. Expects coerced
    (datetime) t_in, exactly what the enumerator holds when it pre-sorts the
    NDJSON payload."""
    return (ep["t_in"], str(ep["body"]), str(ep["relation"]),
            json.dumps(ep, sort_keys=True, separators=(",", ":"), default=str))


def _open_binary_uri(uri: str, *, gcs_client=None):
    """A readable binary stream for a local path or a gs://bucket/object URI
    (the REAL streamed code path: google-cloud-storage blob.open, imported
    lazily so local runs never require the library; `gcs_client` is the
    test-injected transport, same call shape as storage.Client)."""
    if uri.startswith("gs://"):
        bucket_name, _, blob_name = uri[5:].partition("/")
        if not bucket_name or not blob_name:
            raise EpisodeStreamError(f"malformed gs:// URI: {uri!r}")
        if gcs_client is not None:
            client = gcs_client
        else:
            from google.cloud import storage  # lazy: sidecar image only
            client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        return blob.open("rb")
    return open(uri, "rb")


def read_text_uri(uri: str, *, gcs_client=None) -> str:
    """Small-document read (manifest, coverage) from a local path or gs://
    URI, streamed through _open_binary_uri."""
    with _open_binary_uri(uri, gcs_client=gcs_client) as fh:
        return io.TextIOWrapper(fh, encoding="utf-8").read()


class EpisodeObjectStream:
    """One per-body NDJSON object as a bounded, verifying stream.

    Iterates parsed episode dicts (times coerced) one line at a time —
    local path or gs:// URI — while accumulating the object's line count,
    byte count, and sha256 over the exact bytes, and VERIFYING the canonical
    per-object order (episode_stream_key non-decreasing line over line). Any
    unparsable line, missing required key, naive instant, or out-of-order
    line raises EpisodeStreamError. After exhaustion, `stats` carries
    {lines, bytes, sha256} for the finalized-manifest binding."""

    REQUIRED_KEYS = ("t_in", "body", "relation", "target_type", "target_ref",
                     "t_out", "independence_group")

    def __init__(self, uri: str, *, gcs_client=None):
        self.uri = uri
        self._gcs_client = gcs_client
        self._hasher = hashlib.sha256()
        self.lines = 0
        self.bytes = 0

    @property
    def stats(self) -> dict:
        return {"lines": self.lines, "bytes": self.bytes,
                "sha256": "sha256:" + self._hasher.hexdigest()}

    def __iter__(self):
        prev_key = None
        try:
            fh = _open_binary_uri(self.uri, gcs_client=self._gcs_client)
        except EpisodeStreamError:
            raise
        except Exception as exc:
            raise EpisodeStreamError(
                f"unreadable episode object {self.uri!r}: {exc}") from exc
        with fh:
            for raw in fh:
                self._hasher.update(raw)
                self.bytes += len(raw)
                line = raw.decode("utf-8").strip()
                if not line:
                    continue
                self.lines += 1
                try:
                    ep = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise EpisodeStreamError(
                        f"{self.uri}:{self.lines}: unparsable NDJSON line: "
                        f"{exc}") from exc
                missing = [k for k in self.REQUIRED_KEYS if k not in ep]
                if missing:
                    raise EpisodeStreamError(
                        f"{self.uri}:{self.lines}: episode missing keys "
                        f"{missing}")
                _coerce_episode_times([ep])
                key = episode_stream_key(ep)
                if prev_key is not None and key < prev_key:
                    raise EpisodeStreamError(
                        f"{self.uri}:{self.lines}: episode object violates "
                        "the canonical per-body stream order (not written by "
                        "the finalized century chain) — rejected, never "
                        "silently re-ordered")
                prev_key = key
                yield ep


def iter_episodes_merged(streams: list[EpisodeObjectStream]):
    """k-way merge of per-body EpisodeObjectStreams into ONE canonical-order
    episode stream. O(len(streams)) memory — never a dataset-scale list.
    After the generator is exhausted each stream's `stats` are final (the
    caller binds them against the finalized input manifest)."""
    iterators = [iter(s) for s in streams]
    heap: list[tuple] = []
    for i, it in enumerate(iterators):
        try:
            ep = next(it)
        except StopIteration:
            continue
        heapq.heappush(heap, (episode_stream_key(ep), i, ep))
    while heap:
        _, i, ep = heapq.heappop(heap)
        yield ep
        try:
            nxt = next(iterators[i])
        except StopIteration:
            continue
        heapq.heappush(heap, (episode_stream_key(nxt), i, nxt))


def coverage_binding(coverage: list[dict]) -> str:
    """Order-independent sha256 binding of the merged coverage rows — the
    finalized manifest records it and the build re-verifies it, so a
    coverage payload that does not match the finalized enumeration cannot
    earn GREEN."""
    canon = sorted(json.dumps(c, sort_keys=True, separators=(",", ":"),
                              default=str) for c in coverage)
    return "sha256:" + hashlib.sha256(
        json.dumps(canon, separators=(",", ":")).encode("utf-8")).hexdigest()


def load_input_manifest(uri: str, *, gcs_client=None) -> dict:
    try:
        return json.loads(read_text_uri(uri, gcs_client=gcs_client))
    except EpisodeStreamError:
        raise
    except Exception as exc:
        raise ManifestVerificationError(
            f"input manifest {uri!r} unreadable/unparsable: {exc}") from exc


def verify_manifest_static(manifest: dict, *, chart_id: str, generation: str,
                           horizon_text: str, expected_bodies) -> list[str]:
    """Everything checkable BEFORE touching the database or the stream
    content (amendment 2): finalization marker, run identity, chart,
    generation, horizon, and the full expected body set each with a uniform
    run_id and a usable object entry. Returns the per-body object URIs in
    expected_bodies order."""
    if not isinstance(manifest, dict):
        raise ManifestVerificationError("input manifest is not a JSON object")
    if manifest.get("finalized") is not True:
        raise ManifestVerificationError(
            "input manifest is not FINALIZED — the enumeration chain did not "
            "complete; an incomplete stream earns nothing (§N.8)")
    run_id = manifest.get("run_id")
    if not run_id:
        raise ManifestVerificationError("input manifest carries no run_id")
    for field, want in (("chart_id", chart_id), ("generation", generation),
                        ("horizon", horizon_text)):
        if manifest.get(field) != want:
            raise ManifestVerificationError(
                f"input manifest {field}={manifest.get(field)!r} != this "
                f"build's {want!r} — refusing a mismatched/mixed build")
    bodies = manifest.get("bodies")
    objects = manifest.get("objects")
    if bodies != list(expected_bodies) or not isinstance(objects, dict):
        raise ManifestVerificationError(
            f"input manifest bodies {bodies!r} != expected "
            f"{list(expected_bodies)!r}")
    uris = []
    for body in expected_bodies:
        entry = objects.get(body)
        if not isinstance(entry, dict) or not entry.get("uri"):
            raise ManifestVerificationError(
                f"input manifest has no finalized object for body {body!r} — "
                "an omitted body fails the build, never GREEN")
        if entry.get("run_id") != run_id:
            raise ManifestVerificationError(
                f"object for {body!r} carries run_id {entry.get('run_id')!r} "
                f"!= manifest run_id {run_id!r} — mixed-run input refuses "
                "the build")
        for stat in ("lines", "bytes", "sha256"):
            if stat not in entry:
                raise ManifestVerificationError(
                    f"object for {body!r} lacks finalized stat {stat!r}")
        uris.append(entry["uri"])
    cov = manifest.get("coverage")
    if not isinstance(cov, dict) or not cov.get("uri") or not cov.get("sha256"):
        raise ManifestVerificationError(
            "input manifest lacks the coverage binding (uri + sha256)")
    return uris


def verify_object_stats(streams: list[EpisodeObjectStream],
                        manifest: dict, expected_bodies) -> None:
    """Post-consumption content binding (amendment 2): each object's streamed
    line count, byte count, and sha256 must equal the finalized manifest's —
    clean-prefix truncation and same-length alteration both fail here."""
    objects = manifest["objects"]
    for body, stream in zip(expected_bodies, streams):
        want = objects[body]
        got = stream.stats
        for stat in ("lines", "bytes", "sha256"):
            if got[stat] != want[stat]:
                raise ManifestVerificationError(
                    f"object for {body!r}: streamed {stat}={got[stat]!r} != "
                    f"finalized manifest {want[stat]!r} — truncated/altered "
                    "input fails the build, never GREEN (§N.8)")


def _synthetic_episodes() -> list[dict]:
    t = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
    from datetime import timedelta
    return [{
        "independence_group": "ig-saturn-rehearsal",
        "body": "Saturn", "relation": "conjunction", "aspect_deg": 0,
        "target_type": "karaka", "target_ref": "SUN", "target_fact_id": None,
        "target_resolution_state": "resolved", "target_longitude_deg": 90.0,
        "t_in": t - timedelta(hours=2),
        "t_exact": t,
        "t_out": t + timedelta(hours=2),
        "bracket_seconds": 300, "tolerance_arcsec": 2.0,
        "truncated_at_horizon": None, "branch": "direct",
        "orb_max_deg": None,  # filled from --orb-deg below
        "orb_source": "orb_conj_slow",
        "epistemic_class": "observed_event",
        "completeness_state": "applied",
        "operator_role": "kernel", "precision_regime": "instant_grain",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "ephemeris_backend": {"backend": "swieph", "retflag": 258},
        "evidence_fact_ids": [],
        "classical_citation": None, "uncited_extension": True,
        "corpus_verifiable": None,
    }]


def _synthetic_coverage(horizon: str) -> list[dict]:
    return [{
        "partition_kind": "body_target", "partition_key": "saturn:karaka",
        "requested_horizon": horizon, "completed_horizon": horizon,
        "resolution": 2.0, "relations_searched": ["conjunction"],
        "targets_requested": 1,
        "target_resolution_state_counts": {"resolved": 1, "unavailable": 0,
                                           "unqualified": 0},
        "unavailable_inputs": {}, "unsearched_reason": None,
    }]


def main(argv: list[str] | None = None, *, gcs_client=None) -> int:
    parser = step_parser(6, __doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default="4.0")
    parser.add_argument("--horizon-start", default="2020-01-01T00:00:00+00:00")
    parser.add_argument("--horizon-end", default="2030-01-01T00:00:00+00:00")
    parser.add_argument("--episodes-json")
    parser.add_argument("--episodes-ndjson",
                        help="path or glob of the per-body NDJSON episode "
                             "files, streamed and order-verified (bounded "
                             "memory); the rehearsal-scale streamed shape — "
                             "the century chain uses --input-manifest. "
                             "Mutually exclusive with --episodes-json and "
                             "--input-manifest")
    parser.add_argument("--input-manifest",
                        help="the FINALIZED century input manifest "
                             "(CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §2): object "
                             "URIs, per-object counts/checksums, run "
                             "identity, horizon, and the coverage binding are "
                             "verified before any candidate success (§N.8). "
                             "Object bodies + coverage come from the manifest "
                             "(--episodes-* and --coverage-json not used)")
    parser.add_argument("--insert-batch-size", type=int, default=10000,
                        help="rows per INSERT batch in the bounded streamed "
                             "write (memory bound, not a correctness input)")
    parser.add_argument("--coverage-json")
    parser.add_argument("--rehearse-synthetic", action="store_true")
    parser.add_argument("--orb-deg", type=float, default=5.0,
                        help="M-1 fallback orb (no-box × 5.0°) until the native "
                             "ratifies WP8 M-1's 1.0° recommendation")
    parser.add_argument("--delta-report", help="§4.11 factor-level delta report "
                        "vs '3.0' — REQUIRED at tranche time (7.C)")
    args = parser.parse_args(argv)

    episode_sources = [bool(args.episodes_json), bool(args.episodes_ndjson),
                       bool(args.input_manifest)]
    if sum(episode_sources) > 1:
        print("ERROR: --episodes-json, --episodes-ndjson, and "
              "--input-manifest are mutually exclusive", file=sys.stderr)
        return 3

    if not (args.rehearse_synthetic
            or (args.input_manifest
                or ((args.episodes_json or args.episodes_ndjson)
                    and args.coverage_json))):
        print("ERROR: provide --episodes-json or --episodes-ndjson, plus "
              "--coverage-json, or --input-manifest (finalized century "
              "chain), or --rehearse-synthetic for rehearsal",
              file=sys.stderr)
        return 3

    vector = dict(GENERATION_VECTOR_FLAGS)
    vector["orb_max_deg"] = args.orb_deg
    vector["orb_ruling"] = ("M-1 fallback no-box × 5.0° (unratified)"
                            if args.orb_deg == 5.0 else "per --orb-deg")
    vector["delta_report"] = args.delta_report

    horizon_text = f"[{args.horizon_start},{args.horizon_end})"
    # The streamed paths feed ledger.write_contacts_streaming; the small
    # monolithic paths keep write_contacts.
    episode_stream = None      # iterator of episode dicts (bounded)
    stream_objects = None      # list[EpisodeObjectStream] for manifest binding
    expected_bodies = None
    manifest = None
    episodes = None            # materialized list (monolithic paths only)

    try:
        if args.rehearse_synthetic:
            episodes = _synthetic_episodes()
            for ep in episodes:
                ep["orb_max_deg"] = args.orb_deg
            coverage = _synthetic_coverage(horizon_text)
        elif args.input_manifest:
            from step06_enumerate_episodes import PERSISTED_BODIES
            expected_bodies = list(PERSISTED_BODIES)
            manifest = load_input_manifest(args.input_manifest,
                                           gcs_client=gcs_client)
            uris = verify_manifest_static(
                manifest, chart_id=args.chart_id,
                generation=args.generation, horizon_text=horizon_text,
                expected_bodies=expected_bodies)
            coverage = json.loads(read_text_uri(manifest["coverage"]["uri"],
                                                gcs_client=gcs_client))
            if coverage_binding(coverage) != manifest["coverage"]["sha256"]:
                raise ManifestVerificationError(
                    "coverage payload does not match the finalized manifest's "
                    "coverage binding — refusing (§N.8)")
            stream_objects = [EpisodeObjectStream(u, gcs_client=gcs_client)
                              for u in uris]
            episode_stream = iter_episodes_merged(stream_objects)
            vector["input_manifest_run_id"] = manifest["run_id"]
        else:
            if args.episodes_ndjson:
                paths = sorted(glob.glob(args.episodes_ndjson))
                if not paths and Path(args.episodes_ndjson).exists():
                    paths = [args.episodes_ndjson]
                if not paths:
                    raise EpisodeStreamError(
                        f"--episodes-ndjson matched no files: "
                        f"{args.episodes_ndjson!r}")
                stream_objects = [EpisodeObjectStream(p) for p in paths]
                episode_stream = iter_episodes_merged(stream_objects)
            else:
                episodes = _coerce_episode_times(
                    json.loads(Path(args.episodes_json).read_text()))
            coverage = json.loads(Path(args.coverage_json).read_text())
    except (ManifestVerificationError, EpisodeStreamError) as exc:
        print(f"REFUSED (input verification): {exc}", file=sys.stderr)
        return 3

    # Coverage insertion order is by partition_key in every mode — the order
    # build_coverage_rows imposes on the monolithic payload (amendment 6).
    coverage = sorted(coverage, key=lambda c: (c["partition_kind"],
                                               c["partition_key"]))

    ledger = _load_ledger()
    conn = connect(args.dsn, step=6, autocommit=False)

    # §12.9 gate — BEFORE any ledger write. Refuses a candidate built on vedha rows
    # whose upstream fingerprint is missing or no longer matches the reference tables.
    if args.rehearse_synthetic:
        vector["vedha_upstream_freshness"] = "NOT_RUN: --rehearse-synthetic"
    else:
        if str(SIDECAR) not in sys.path:  # this file runs as a standalone script
            sys.path.insert(0, str(SIDECAR))
        from services.ka_vedha_gochara.freshness import (
            check_overlay_freshness, gate_allows_overlays)
        reports = check_overlay_freshness(conn, args.chart_id)
        conn.rollback()  # the checks only read; leave no open transaction
        vector["vedha_upstream_freshness"] = reports["house_vedha"].state
        vector["moorti_upstream_freshness"] = reports["moorti"].state
        vector["vedha_upstream_fingerprint"] = reports["house_vedha"].current
        vector["moorti_upstream_fingerprint"] = reports["moorti"].current
        if not gate_allows_overlays(reports):
            detail = "; ".join(f"{name}: {r.summary()}" for name, r in reports.items())
            print(f"REFUSED (§12.9): {detail}. A candidate must not be built on stale overlay rows "
                  "— rebuild ka_vedha_gochara and ka_moorti_nirnaya first.", file=sys.stderr)
            conn.close()
            return 7
    build_id = f"wp10-step6-{int(time.time())}"
    try:
        cid = ledger.register_convention(conn, CONVENTION_VECTOR,
                                         {"ephemeris_backend": "swieph",
                                          "retflag": 258})
        manifest_id = ledger.publish_candidate(
            conn, args.chart_id, args.generation, cid, vector,
            {"backend": "swieph", "retflag": 258}, horizon_text)
        if episode_stream is not None:
            n_contacts = ledger.write_contacts_streaming(
                conn, args.chart_id, args.generation, cid,
                episode_stream, build_id, batch_size=args.insert_batch_size)
        else:
            n_contacts = len(ledger.write_contacts(
                conn, args.chart_id, args.generation, cid, episodes, build_id))
        # §N.8: the finalized-manifest content binding verifies AFTER the
        # stream is fully consumed and BEFORE the commit — a truncated,
        # altered, or unreadable object rolls the whole transaction back and
        # never earns GREEN.
        if manifest is not None:
            verify_object_stats(stream_objects, manifest, expected_bodies)
        n_cov = ledger.write_coverage(conn, args.chart_id, args.generation, cid,
                                      coverage, build_id)
        conn.commit()
    except ledger.PublishedGenerationRefusal as exc:
        conn.rollback()
        print(f"REFUSED: {redact_text(exc)}", file=sys.stderr)
        conn.close()
        return 6
    except (ManifestVerificationError, EpisodeStreamError) as exc:
        conn.rollback()
        conn.close()
        print(f"REFUSED (input verification): {redact_text(exc)} — the "
              "candidate build failed, rolled back, and earns no GREEN "
              "(§N.8)", file=sys.stderr)
        return 3
    except Exception as exc:
        conn.rollback()
        conn.close()
        # ADK-0020 residual: the relation's primary key rejects a duplicate
        # contact_id in a (corrupt) stream — the dedupe refusal surface.
        if type(exc).__name__ == "IntegrityError":
            print(f"REFUSED (ADK-0020): the ledger primary key rejected a "
                  f"duplicate/invalid contact row: {redact_text(exc)}",
                  file=sys.stderr)
            return 5
        raise
    conn.close()

    report = {
        "chart_id": args.chart_id, "generation": args.generation,
        "convention_id": cid, "manifest_id": manifest_id,
        "build_id": build_id, "contacts_written": n_contacts,
        "coverage_rows_written": n_cov,
        "input_generation_vector": vector,
    }
    if manifest is not None:
        report["input_manifest"] = {
            "run_id": manifest["run_id"],
            "objects_verified": len(stream_objects),
            "verification": "finalized manifest: bodies, run identity, "
                            "horizon, coverage binding, and per-object "
                            "lines/bytes/sha256 all verified before commit",
        }
    print(json.dumps(report, indent=2, default=str))
    if args.evidence:
        write_evidence(6, "GREEN",
                       f"```json\n{json.dumps(report, indent=2, default=str)}\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
