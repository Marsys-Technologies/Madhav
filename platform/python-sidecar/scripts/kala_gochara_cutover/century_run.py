#!/usr/bin/env python3
"""century_run.py — Pravāha A2.5 century execution-chain driver (chart
482012f1-710e-4a25-994a-93821f5871aa, generation '4.1'), implementing
CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §3 as amended by ASTRA_REVIEW_A2_5_STREAMING
v1.0 and v1.1.

Chain (per A2.5 run, one Cloud Run job execution with a container override):

  1. loop PERSISTED_BODIES (the eight non-Moon grahas, imported from
     step06_enumerate_episodes — never restated here): step06 enumeration with
     --bodies <body> --episodes-ndjson-out <run_dir>/episodes/<body>.ndjson
     --coverage-out <run_dir>/coverage/<body>.json --receipt-out
     <run_dir>/episodes/<body>.receipt.json (streaming per-body append;
     per-body peak memory only, spec §2.2, under the memory guard below);
  2. after EACH body: REQUIRE the completion receipt step06 wrote, verify it
     against the object's independently streamed lines/bytes/sha256, the
     body's coverage partitions/horizon, and the run's provenance (the FIRST
     body's configuration / source snapshot / ephemeris checksums /
     convention id bind the run; any later body that disagrees is a
     mixed-source run and refuses); upload the NDJSON, its receipt and its
     .dropped_refs.json dedupe-provenance sidecar to <gcs-prefix>/<attempt>/
     with CREATE-ONLY preconditions, verify the landed sizes, then DELETE the
     local object — /tmp is RAM-backed tmpfs on Cloud Run (F-185);
  3. write the FINALIZED input manifest (CENTURY_INPUT_MANIFEST v1.1: attempt
     identity, chart, generation, horizon, expected bodies, per-object
     lines/bytes/sha256 + receipt binding + dedupe-provenance binding, the
     coverage binding with partitions per body, and the run-level
     provenance) — written ONLY after every body succeeded and verified;
  4. ONE candidate build (step06_candidate_build.py --input-manifest <gs://
     manifest>): a bounded streamed k-way merge from GCS into one candidate
     transaction, every binding above re-verified before any success (§N.8);
  5. step06a_class_context.py (streamed per-class instants) →
     step06b_windows_projection.py (per-cluster streaming) with
     --delta-report-out.

Exit codes propagate per step, unchanged: 7 = §12.9 stale-overlay refusal,
6 = publish refusal, 5 = ADK-0020/0021/0022 dedupe refusal, 4 = production
guard (inherited from common.connect), 3 = cannot proceed / guard refusal.
The first nonzero step exit aborts the chain with that code; no manifest is
finalized and no build is attempted.

GUARDS — all evaluated BEFORE any filesystem or subprocess work; each refusal
exits 3:
  * env PRAVAHA_CENTURY_RUN_AUTHORIZED=1 (ADK-0028: the marker the Cloud Run
    job's container override sets, spec §3; absent anywhere else);
  * the requested horizon IS the pinned century window
    [1984-02-05T00:00:00+00:00, 2084-02-05T00:00:00+00:00);
  * --chart-id IS the canonical 482012f1-710e-4a25-994a-93821f5871aa
    (ADK-0029) and --generation IS '4.1' (ADK-0027);
  * --gcs-prefix is REQUIRED: the century path stages EXTERNALLY, always
    (round-2 amendment 1 — the local-retention route was itself an unbounded
    century-scale tmpfs footprint and is gone).

Memory (round-2 amendment 1): every child runs under an RLIMIT_AS guard
(--memory-guard-gib, default 14 GiB, below the job's 16 GiB) so an overrun
fails LOUDLY as exit 3 inside the child rather than an OOM-kill; after every
step the driver reads the children's peak RSS (RUSAGE_CHILDREN) into the
chain report and refuses to continue if it exceeded the guard. The per-body
enumeration is inherently input-sized (the ADK-0020 dedupe and the canonical
sort need the whole body's payload) — that is WHY the guard exists; the build
and the projection are bounded by construction (batch / overlap cluster).

DSN hygiene (amendments 3 + r2-3): command lines are logged ONLY through
common.redact_argv; every child's stdout AND stderr are forwarded line by
line (still streaming — each line is emitted the moment the child writes
it) through common.redact_text, which scrubs every libpq credential form and
the literal secret of THIS run's --dsn; every driver diagnostic and the chain
report pass through the same redactor; uncaught exceptions are reported via
common.run_main_guarded (redacted).

Attempt artifacts (amendment 5 + r2-4): attempt_id =
pravaha-a25-century-<UTC stamp>-<96-bit random> (collision-resistant across
containers starting in the same second); the local run directory is created
EXCLUSIVELY (mkdir exist_ok=False — any pre-existing directory refuses); every
remote object is created with if_generation_match=0 (create-only) — a second
attempt can never overwrite an object an earlier finalized manifest
references; a collision refuses this attempt (exit 3) and leaves the earlier
artifacts byte-identical. Resume semantics per spec §3: re-run is a fresh
attempt and a fresh build of the same generation label — candidate rows are
replaced in one transaction, never edited in place (N-7).

Usage (inside the Cloud Run job only):
    PRAVAHA_CENTURY_RUN_AUTHORIZED=1 \\
    python3 scripts/kala_gochara_cutover/century_run.py \\
        --dsn postgresql://... \\
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa --generation 4.1 \\
        --gcs-prefix gs://gochara-century-stream/kala_gochara/482012f1/4.1/episodes \\
        [--workdir /tmp/century] [--orb-deg 5.0] [--ephe-path ...] \\
        [--memory-guard-gib 14] [--delta-report path] [--evidence]

Exit codes: 0 chain complete; 3 guard refusal / cannot proceed; otherwise the
failing step's exit code propagates verbatim.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from common import (  # noqa: E402
    DEFAULT_MEMORY_GUARD_BYTES, RedactingArgumentParser, file_stats,
    peak_rss_bytes, redact_argv, redact_text, run_main_guarded,
)
from step06_enumerate_episodes import PERSISTED_BODIES  # noqa: E402
from step06_candidate_build import (  # noqa: E402
    MANIFEST_ARTIFACT, MANIFEST_VERSION, ManifestVerificationError,
    PROVENANCE_KEYS, coverage_binding, receipt_provenance, verify_coverage_rows,
    verify_receipt,
)

# The pinned century window (CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 header / f0p2
# evidence step 1; no narrowing ruling exists).
CENTURY_HORIZON_START = "1984-02-05T00:00:00+00:00"
CENTURY_HORIZON_END = "2084-02-05T00:00:00+00:00"

# Scope (amendment 4): exactly this chart, exactly this generation — enforced
# before any filesystem or subprocess work.
CANONICAL_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
CENTURY_GENERATION = "4.1"

AUTHORIZATION_ENV = "PRAVAHA_CENTURY_RUN_AUTHORIZED"

STEP06 = HERE / "step06_enumerate_episodes.py"
STEP06_BUILD = HERE / "step06_candidate_build.py"
STEP06A = HERE / "step06a_class_context.py"
STEP06B = HERE / "step06b_windows_projection.py"

UTC = timezone.utc

# _step's return when a child exited 0 but its peak RSS exceeded the guard —
# distinct from every real returncode (a signal-killed child returns -N).
MEMORY_GUARD_EXCEEDED = "MEMORY_GUARD_EXCEEDED"


def new_attempt_id() -> str:
    """Collision-resistant attempt identity (amendment r2-4): a UTC second
    stamp for humans plus 96 random bits — two containers starting in the
    same second cannot share a prefix."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"pravaha-a25-century-{stamp}-{uuid.uuid4().hex[:24]}"


_object_stats = file_stats  # the receipt/manifest/build share one detector


class AttemptArtifactCollision(RuntimeError):
    """A create-only upload found the object already present: another attempt
    shares this prefix. This attempt refuses; the existing object (possibly
    referenced by a finalized manifest) is left byte-identical."""


def upload_file_to_gcs(gcs_prefix: str, local_path: Path, blob_name: str,
                       *, gcs_client=None, verify_bytes: int | None = None
                       ) -> str:
    """Create-only upload of one file to gs://<bucket>/<prefix>/<blob_name>;
    returns the gs:// URI. The bucket is used AS-IS via client.bucket(...) —
    buckets are NEVER created here (bucket choice and grants are native
    infra, spec pre-flight checklist). google-cloud-storage is imported
    lazily so local rehearsals never require it; `gcs_client` is the
    test-injected transport with the same call shape.

    if_generation_match=0 (amendment r2-4): the object must not exist; a
    412 PreconditionFailed raises AttemptArtifactCollision. The landed
    blob's size is always re-read and must equal the local file's — a
    short/failed upload refuses the run rather than finalizing a truncated
    object."""
    if not gcs_prefix.startswith("gs://"):
        raise ValueError(f"--gcs-prefix must be gs://<bucket>/<prefix>, got "
                         f"{gcs_prefix!r}")
    if gcs_client is not None:
        client = gcs_client
    else:
        from google.cloud import storage  # lazy: sidecar image only
        client = storage.Client()
    bucket_name, _, prefix = gcs_prefix[5:].partition("/")
    dest = f"{prefix.rstrip('/')}/{blob_name}" if prefix else blob_name
    blob = client.bucket(bucket_name).blob(dest)  # never create_bucket
    want = verify_bytes if verify_bytes is not None else Path(local_path).stat().st_size
    try:
        blob.upload_from_filename(str(local_path), if_generation_match=0)
    except Exception as exc:  # noqa: BLE001 — classified below
        if getattr(exc, "code", None) == 412 or type(exc).__name__ == "PreconditionFailed":
            raise AttemptArtifactCollision(
                f"object gs://{bucket_name}/{dest} already exists — another "
                "attempt shares this prefix; refusing to overwrite (create-only "
                "upload, if_generation_match=0)") from exc
        raise
    blob.reload()
    if blob.size != want:
        raise RuntimeError(
            f"uploaded object gs://{bucket_name}/{dest} has size "
            f"{blob.size} != local {want} — upload verification failed; "
            "refusing to finalize a truncated object")
    return f"gs://{bucket_name}/{dest}"


def _emit(line: str) -> None:
    sys.stdout.write(line)
    sys.stdout.flush()


def _run(argv: list[str], *, on_line=None) -> int:
    """Run one chain step. The command line is logged redacted; the child's
    stdout AND stderr are forwarded line by line THROUGH redact_text as the
    child writes them (streaming preserved — nothing is buffered to the
    child's exit), so a credential the child prints in any form never
    reaches the job log."""
    print("+ " + " ".join(redact_argv(argv)), flush=True)
    proc = subprocess.Popen(argv, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1,
                            errors="replace")
    sink = on_line or _emit
    with proc.stdout:
        for line in proc.stdout:
            sink(redact_text(line))
    return proc.wait()


def _uniform_provenance_check(bound: dict | None, body: str,
                              receipt: dict) -> dict:
    prov = receipt_provenance(receipt)
    if bound is None:
        return prov
    if prov != bound:
        diff = [k for k in PROVENANCE_KEYS if prov.get(k) != bound.get(k)]
        raise ManifestVerificationError(
            f"body {body!r} was enumerated under different {diff} than the "
            "bodies before it — a mixed-source/mixed-configuration run "
            "cannot be finalized")
    return bound


def main(argv: list[str] | None = None, *, gcs_client=None) -> int:
    parser = RedactingArgumentParser(description=__doc__)
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default=CENTURY_GENERATION)
    parser.add_argument("--horizon-start", default=CENTURY_HORIZON_START)
    parser.add_argument("--horizon-end", default=CENTURY_HORIZON_END)
    parser.add_argument("--orb-deg", type=float, default=5.0)
    parser.add_argument("--ephe-path", default=None,
                        help="forwarded to step06 (its own default is the "
                             "pinned local set when omitted)")
    parser.add_argument("--workdir", default=None,
                        help="local staging root (default "
                             "./century_run_<chart-id>_<generation>); each "
                             "attempt stages under an EXCLUSIVELY created "
                             "<workdir>/<attempt_id>/")
    parser.add_argument("--gcs-prefix", default=None,
                        help="gs://<bucket>/<prefix> for the per-body objects "
                             "(REQUIRED: the century path stages externally, "
                             "always)")
    parser.add_argument("--memory-guard-gib", type=float,
                        default=DEFAULT_MEMORY_GUARD_BYTES / (1 << 30),
                        help="RLIMIT_AS guard forwarded to every child and "
                             "the driver's per-step peak-RSS ceiling (0 = no "
                             "guard; default 14, under the job's 16 GiB)")
    parser.add_argument("--delta-report", default=None,
                        help="§4.11 factor-level delta report vs '3.0', "
                             "forwarded to the candidate build (7.C: required "
                             "at tranche time)")
    parser.add_argument("--evidence", action="store_true")
    args = parser.parse_args(argv)

    # ── Guards (ADK-0027/0028/0029 + amendment 4 + r2-1) — before ANY
    # filesystem or subprocess work.
    if os.environ.get(AUTHORIZATION_ENV) != "1":
        print(f"REFUSED (ADK-0028): century enumeration runs ONLY as the "
              f"Cloud Run job execution (CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §3), "
              f"which sets {AUTHORIZATION_ENV}=1. Local century enumeration is "
              "prohibited, always. Decade-scale rehearsals use "
              "step06_enumerate_episodes.py directly.", file=sys.stderr)
        return 3
    if (args.horizon_start, args.horizon_end) != (CENTURY_HORIZON_START,
                                                  CENTURY_HORIZON_END):
        print(f"REFUSED (ADK-0028): the century window is pinned to "
              f"[{CENTURY_HORIZON_START}, {CENTURY_HORIZON_END}) — got "
              f"[{args.horizon_start}, {args.horizon_end}). This driver runs "
              "the pinned century only.", file=sys.stderr)
        return 3
    if args.chart_id != CANONICAL_CHART_ID:
        print(f"REFUSED (ADK-0029): the century build is scoped to chart "
              f"{CANONICAL_CHART_ID} exactly — got {args.chart_id!r}. No "
              "other chart is enumerated by this driver, ever.",
              file=sys.stderr)
        return 3
    if args.generation != CENTURY_GENERATION:
        print(f"REFUSED (ADK-0027): the century build's generation label is "
              f"{CENTURY_GENERATION!r} exactly (chart-1 '4.0' is burned) — "
              f"got {args.generation!r}.", file=sys.stderr)
        return 3
    if not args.gcs_prefix or not args.gcs_prefix.startswith("gs://"):
        print("REFUSED (external staging required): the century path stages "
              "every per-body object in GCS (--gcs-prefix gs://<bucket>/"
              "<prefix>); retaining century-scale objects on the job's "
              "RAM-backed /tmp is not a permitted shape (round-2 amendment 1).",
              file=sys.stderr)
        return 3
    guard_bytes = int(args.memory_guard_gib * (1 << 30)) if args.memory_guard_gib > 0 else 0

    # ── Fresh, exclusively created per-attempt staging (amendment r2-4).
    attempt_id = new_attempt_id()
    workdir = Path(args.workdir
                   or f"century_run_{args.chart_id}_{args.generation}")
    run_dir = workdir / attempt_id
    try:
        workdir.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(exist_ok=False)
    except FileExistsError:
        print(f"REFUSED (retry safety): attempt directory {run_dir} already "
              "exists — every attempt stages under an EXCLUSIVELY created "
              "directory; a colliding attempt id refuses rather than mixing "
              "attempts' streams.", file=sys.stderr)
        return 3
    episodes_dir = run_dir / "episodes"
    coverage_dir = run_dir / "coverage"
    episodes_dir.mkdir()
    coverage_dir.mkdir()
    gcs_run_prefix = f"{args.gcs_prefix.rstrip('/')}/{attempt_id}"
    horizon_text = f"[{args.horizon_start},{args.horizon_end})"

    chain_report: dict = {
        "driver": "century_run",
        "spec": "CENTURY_CLOUD_RUN_JOB_SPEC_v1_0",
        "chart_id": args.chart_id, "generation": args.generation,
        "horizon": horizon_text,
        "attempt_id": attempt_id, "run_id": attempt_id,
        "run_dir": str(run_dir), "gcs_run_prefix": gcs_run_prefix,
        "bodies": list(PERSISTED_BODIES),
        "memory_guard_bytes": guard_bytes,
        "steps": [], "gcs_uploads": [],
    }

    def _report() -> None:
        print(redact_text(json.dumps(chain_report, indent=2, default=str)),
              flush=True)

    def _abort(msg: str, rc: int) -> int:
        print(redact_text(msg), file=sys.stderr, flush=True)
        _report()
        return rc

    def _step(name: str, argv: list[str]):
        rc = _run(argv)
        peak = peak_rss_bytes(children=True)
        chain_report["steps"].append({"step": name, "exit": rc,
                                      "children_peak_rss_bytes": peak})
        if rc < 0:
            # killed by a signal (an OOM-kill is SIGKILL = -9): surfaced as a
            # named driver refusal, never re-raised as a negative exit
            chain_report["steps"][-1]["signal"] = -rc
            print(f"{name}: child killed by signal {-rc} (an OOM-kill is 9) — "
                  "treated as a memory/infrastructure failure", file=sys.stderr,
                  flush=True)
            return 3
        if rc == 0 and guard_bytes and peak is not None and peak > guard_bytes:
            chain_report["steps"][-1]["memory_guard"] = "EXCEEDED"
            return MEMORY_GUARD_EXCEEDED
        return rc

    def _upload(local: Path, blob_name: str) -> str:
        uri = upload_file_to_gcs(gcs_run_prefix, local, blob_name,
                                 gcs_client=gcs_client)
        chain_report["gcs_uploads"].append(uri)
        return uri

    common = ["--dsn", args.dsn, "--chart-id", args.chart_id,
              "--generation", args.generation,
              "--horizon-start", args.horizon_start,
              "--horizon-end", args.horizon_end]
    if args.evidence:
        common.append("--evidence")
    guard_argv = (["--memory-guard-bytes", str(guard_bytes)] if guard_bytes
                  else [])

    # 1. per-body enumeration, streaming NDJSON out (spec §2.2); 2. verify
    #    the completion receipt, upload create-only + free the local object.
    objects: dict[str, dict] = {}
    bound_provenance: dict | None = None
    partitions_by_body: dict[str, int] = {}
    for body in PERSISTED_BODIES:
        ndjson = episodes_dir / f"{body}.ndjson"
        receipt_path = episodes_dir / f"{body}.receipt.json"
        cov_path = coverage_dir / f"{body}.json"
        step_argv = [sys.executable, str(STEP06), *common,
                     "--orb-deg", str(args.orb_deg),
                     "--bodies", body,
                     "--episodes-ndjson-out", str(ndjson),
                     "--coverage-out", str(cov_path),
                     "--receipt-out", str(receipt_path), *guard_argv]
        if args.ephe_path:
            step_argv += ["--ephe-path", args.ephe_path]
        rc = _step(f"step06_enumerate_episodes[{body}]", step_argv)
        if rc is MEMORY_GUARD_EXCEEDED:
            return _abort(f"century_run aborted: enumeration of {body} "
                          f"exceeded the memory guard ({guard_bytes} bytes "
                          "peak RSS) — refusing to continue toward the "
                          "container limit; no manifest is finalized", 3)
        if rc != 0:
            return _abort(f"century_run aborted: enumeration of {body} exited "
                          f"{rc} — no input manifest is finalized and no "
                          "candidate build is attempted (§N.8)", rc)
        # completion receipt (amendment r2-2): required, and bound to THIS object
        try:
            if not ndjson.exists():
                raise ManifestVerificationError(
                    f"enumeration of {body} exited 0 but wrote no object")
            if not receipt_path.exists():
                raise ManifestVerificationError(
                    f"enumeration of {body} exited 0 but wrote no completion "
                    "receipt — an exit code is not a completion signal (§N.8)")
            stats = file_stats(ndjson)
            receipt = json.loads(receipt_path.read_text())
            verify_receipt(receipt, body=body, chart_id=args.chart_id,
                           generation=args.generation,
                           horizon_text=horizon_text, object_stats=stats)
            if receipt["configuration"]["orb_deg"] != args.orb_deg:
                raise ManifestVerificationError(
                    f"receipt for {body!r} declares orb_deg="
                    f"{receipt['configuration']['orb_deg']!r} != this run's "
                    f"{args.orb_deg!r}")
            bound_provenance = _uniform_provenance_check(bound_provenance,
                                                         body, receipt)
            coverage_rows = json.loads(cov_path.read_text())
            n_parts = verify_coverage_rows(coverage_rows,
                                           horizon_text=horizon_text,
                                           expected_bodies=[body])[body]
            if n_parts != receipt["coverage"]["partitions"] \
                    or coverage_binding(coverage_rows) != receipt["coverage"]["sha256"]:
                raise ManifestVerificationError(
                    f"coverage for {body!r} ({n_parts} partitions) does not "
                    "match its receipt's coverage binding")
            partitions_by_body[body] = n_parts
            dropped_refs = Path(str(ndjson) + ".dropped_refs.json")
            dd = receipt["dedupe"]
            if dd["dropped_refs_artifact"]:
                if not dropped_refs.exists():
                    raise ManifestVerificationError(
                        f"receipt for {body!r} names a dedupe sidecar that is "
                        "not on disk — provenance lost")
                dr_stats = file_stats(dropped_refs)
                if (dr_stats["sha256"], dr_stats["bytes"]) != (
                        dd["dropped_refs_sha256"], dd["dropped_refs_bytes"]):
                    raise ManifestVerificationError(
                        f"dedupe sidecar for {body!r} does not match its "
                        "receipt binding")
            elif dropped_refs.exists():
                raise ManifestVerificationError(
                    f"a dedupe sidecar exists for {body!r} that its receipt "
                    "does not attest — inconsistent provenance")
        except ManifestVerificationError as exc:
            return _abort(f"century_run aborted (receipt verification, "
                          f"{body}): {exc} — no input manifest is finalized", 3)

        entry = {**stats, "run_id": attempt_id,
                 "episodes_after_dedupe": receipt["episodes"]["episodes_after_dedupe"]}
        try:
            entry["uri"] = _upload(ndjson, f"episodes/{body}.ndjson")
            r_stats = file_stats(receipt_path)
            entry["receipt"] = {
                "uri": _upload(receipt_path, f"episodes/{body}.receipt.json"),
                "bytes": r_stats["bytes"], "sha256": r_stats["sha256"]}
            if dd["dropped_refs_artifact"]:
                entry["dropped_refs"] = {
                    "uri": _upload(dropped_refs,
                                   f"episodes/{body}.ndjson.dropped_refs.json"),
                    "bytes": dd["dropped_refs_bytes"],
                    "sha256": dd["dropped_refs_sha256"]}
            else:
                entry["dropped_refs"] = None
        except AttemptArtifactCollision as exc:
            return _abort(f"century_run aborted (attempt collision, {body}): "
                          f"{exc}", 3)
        except Exception as exc:  # noqa: BLE001 — upload transport failures
            return _abort(f"century_run aborted: GCS upload of {body} "
                          f"failed: {exc}", 3)
        # /tmp is RAM-backed tmpfs (F-185): the century-scale local files are
        # deleted once the verified uploads land — only the small receipt and
        # coverage documents stay for the finalization step.
        ndjson.unlink()
        if dropped_refs.exists():
            dropped_refs.unlink()
        objects[body] = entry

    # 3. merge coverage (sorted by partition_key — the monolithic order,
    #    amendment 6), verify it over ALL bodies, finalize the manifest.
    coverage: list[dict] = []
    for body in PERSISTED_BODIES:
        coverage.extend(json.loads((coverage_dir / f"{body}.json").read_text()))
    coverage.sort(key=lambda c: (c["partition_kind"], c["partition_key"]))
    try:
        merged_by_body = verify_coverage_rows(coverage, horizon_text=horizon_text,
                                              expected_bodies=PERSISTED_BODIES)
        if merged_by_body != partitions_by_body:
            raise ManifestVerificationError(
                f"merged coverage partitions {merged_by_body} != per-body "
                f"{partitions_by_body}")
    except ManifestVerificationError as exc:
        return _abort(f"century_run aborted (coverage verification): {exc}", 3)
    merged_coverage = run_dir / "coverage.json"
    merged_coverage.write_text(json.dumps(coverage, indent=2, default=str) + "\n")
    cov_entry = {"uri": None,
                 "sha256": coverage_binding(coverage),
                 "partitions": len(coverage),
                 "partitions_by_body": partitions_by_body}
    try:
        cov_entry["uri"] = _upload(merged_coverage, "coverage.json")
    except Exception as exc:  # noqa: BLE001
        return _abort(f"century_run aborted: coverage upload failed: {exc}", 3)

    assert bound_provenance is not None  # eight bodies verified above
    manifest = {
        "artifact": MANIFEST_ARTIFACT, "version": MANIFEST_VERSION,
        "finalized": True,
        "run_id": attempt_id, "attempt_id": attempt_id,
        "chart_id": args.chart_id, "generation": args.generation,
        "horizon": horizon_text,
        "bodies": list(PERSISTED_BODIES),
        "objects": objects,
        "coverage": cov_entry,
        **bound_provenance,
        "driver": {"spec": "CENTURY_CLOUD_RUN_JOB_SPEC_v1_0",
                   "delta_report": args.delta_report,
                   "memory_guard_bytes": guard_bytes},
    }
    manifest_path = run_dir / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    try:
        manifest_uri = _upload(manifest_path, "input_manifest.json")
    except Exception as exc:  # noqa: BLE001
        return _abort(f"century_run aborted: manifest upload failed: {exc}", 3)
    chain_report["input_manifest"] = manifest_uri
    chain_report["input_manifest_local"] = str(manifest_path)

    # 4. ONE candidate build from the finalized, uploaded manifest (spec
    #    §2.3): bounded streamed k-way merge FROM GCS, single transaction,
    #    every binding re-verified before any success (§N.8).
    build_argv = [sys.executable, str(STEP06_BUILD), *common,
                  "--orb-deg", str(args.orb_deg),
                  "--input-manifest", manifest_uri, *guard_argv]
    if args.delta_report:
        build_argv += ["--delta-report", args.delta_report]
    rc = _step("step06_candidate_build", build_argv)
    if rc is MEMORY_GUARD_EXCEEDED:
        return _abort("century_run aborted: candidate build exceeded the "
                      "memory guard", 3)
    if rc != 0:
        return _abort(f"century_run aborted: candidate build exited {rc}", rc)

    # 5. class context → windows projection → the delta report (spec §3).
    class_context = run_dir / "class_context.json"
    rc = _step("step06a_class_context",
               [sys.executable, str(STEP06A), "--dsn", args.dsn,
                "--chart-id", args.chart_id, "--generation", args.generation,
                "--out", str(class_context), *guard_argv]
               + (["--evidence"] if args.evidence else []))
    if rc is MEMORY_GUARD_EXCEEDED:
        return _abort("century_run aborted: class context exceeded the "
                      "memory guard", 3)
    if rc != 0:
        return _abort(f"century_run aborted: class context exited {rc}", rc)

    delta_report_out = run_dir / "windows_delta_report.md"
    rc = _step("step06b_windows_projection",
               [sys.executable, str(STEP06B), *common,
                "--orb-deg", str(args.orb_deg),
                "--class-context-json", str(class_context),
                "--delta-report-out", str(delta_report_out), *guard_argv])
    if rc is MEMORY_GUARD_EXCEEDED:
        return _abort("century_run aborted: windows projection exceeded the "
                      "memory guard", 3)
    if rc != 0:
        return _abort(f"century_run aborted: windows projection exited {rc}",
                      rc)

    chain_report["delta_report"] = str(delta_report_out)
    chain_report["status"] = "COMPLETE"
    _report()
    return 0


if __name__ == "__main__":
    sys.exit(run_main_guarded(main))
