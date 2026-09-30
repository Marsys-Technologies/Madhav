#!/usr/bin/env python3
"""century_run.py — Pravāha A2.5 century execution-chain driver (chart
482012f1-710e-4a25-994a-93821f5871aa, generation '4.1'), implementing
CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §3.

Chain (per A2.5 run, one Cloud Run job execution with a container override):

  1. loop PERSISTED_BODIES (the eight non-Moon grahas, imported from
     step06_enumerate_episodes — never restated here): step06 enumeration with
     --bodies <body> --episodes-ndjson-out <run_dir>/episodes/<body>.ndjson
     (streaming per-body append; per-body peak memory only, spec §2.2) and
     --coverage-out <run_dir>/coverage/<body>.json;
  2. after EACH body: stream-compute the object's lines/bytes/sha256, upload
     the NDJSON (and its .dropped_refs.json dedupe-provenance sidecar) to
     <gcs-prefix>/<run_id>/episodes/, verify the landed blob size, then DELETE
     the local files — /tmp is RAM-backed tmpfs on Cloud Run (F-185), so
     retaining per-body files is itself century-scale memory;
  3. write the FINALIZED input manifest (run identity, chart, generation,
     horizon, expected bodies, per-object lines/bytes/sha256, coverage
     binding, input snapshot) — written ONLY after every body succeeded;
  4. ONE candidate build (step06_candidate_build.py --input-manifest): a
     bounded streamed k-way merge from GCS (or the local run dir) into one
     candidate transaction, the manifest verified before any success (§N.8);
  5. step06a_class_context.py → step06b_windows_projection.py (per-class
     server-side-cursor streaming) with --delta-report-out.

Exit codes propagate per step, unchanged: 7 = §12.9 stale-overlay refusal,
6 = publish refusal, 5 = ADK-0020/0021/0022 dedupe refusal, 4 = production
guard (inherited from common.connect), 3 = cannot proceed. The first nonzero
step exit aborts the chain with that code; no manifest is finalized and no
build is attempted.

GUARDS — all evaluated BEFORE any filesystem or subprocess work (ASTRA A2.5
review amendment 4); each refusal exits 3:
  * env PRAVAHA_CENTURY_RUN_AUTHORIZED=1 (ADK-0028: the marker the Cloud Run
    job's container override sets, spec §3; absent anywhere else);
  * the requested horizon IS the pinned century window
    [1984-02-05T00:00:00+00:00, 2084-02-05T00:00:00+00:00);
  * --chart-id IS the canonical 482012f1-710e-4a25-994a-93821f5871aa
    (ADK-0029: scope is one chart; any other chart id is refused, not
    defaulted);
  * --generation IS '4.1' (ADK-0027: chart-1 '4.0' is burned).

DSN hygiene (amendment 3): subprocess command lines are logged ONLY through
common.redact_argv and every failure diagnostic through common.redact_text —
a password-bearing connection string never reaches stdout/stderr.

Retry safety (amendment 5): every attempt runs under a FRESH run identity —
run_id = pravaha-a25-century-<epoch> — with its own local run directory
<workdir>/<run_id>/ and its own GCS object prefix <gcs-prefix>/<run_id>/; a
pre-existing non-empty run directory refuses the run (a caller reusing one
would mix attempts' appends). Incomplete output (a crashed attempt's objects
with no finalized manifest) is distinguished from finalized output BY the
manifest: the build consumes only a manifest that names every expected body
with verified counts/checksums under one run_id; dedupe provenance
(.dropped_refs.json per body) is uploaded alongside each object. Resume
semantics per spec §3: re-run is a fresh build of the same generation label —
candidate rows are replaced in one transaction, never edited in place (N-7).

Usage (inside the Cloud Run job only):
    PRAVAHA_CENTURY_RUN_AUTHORIZED=1 \
    python3 scripts/kala_gochara_cutover/century_run.py \
        --dsn postgresql://... \
        --chart-id 482012f1-710e-4a25-994a-93821f5871aa --generation 4.1 \
        [--workdir /tmp/century] [--gcs-prefix gs://<build-artifacts>/kala_gochara/482012f1/4.1/episodes] \
        [--orb-deg 5.0] [--ephe-path ...] [--delta-report path] [--evidence]

Exit codes: 0 chain complete; 3 guard refusal / cannot proceed; otherwise the
failing step's exit code propagates verbatim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from common import redact_argv, redact_text  # noqa: E402
from step06_enumerate_episodes import PERSISTED_BODIES  # noqa: E402
from step06_candidate_build import coverage_binding  # noqa: E402

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


def _object_stats(path: Path) -> dict:
    """Streamed lines/bytes/sha256 of one local NDJSON object — the binding
    the finalized manifest records and the build re-verifies."""
    hasher = hashlib.sha256()
    nbytes = 0
    lines = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            hasher.update(chunk)
            nbytes += len(chunk)
            lines += chunk.count(b"\n")
    return {"lines": lines, "bytes": nbytes,
            "sha256": "sha256:" + hasher.hexdigest()}


def upload_file_to_gcs(gcs_prefix: str, local_path: Path, blob_name: str,
                       *, gcs_client=None, verify_bytes: int | None = None
                       ) -> str:
    """Upload one file to gs://<bucket>/<prefix>/<blob_name> and return the
    gs:// URI. The bucket is used AS-IS via client.bucket(...) — buckets are
    NEVER created here (bucket choice and grants are native infra, spec
    pre-flight checklist). google-cloud-storage is imported lazily so local
    rehearsals never require it; `gcs_client` is the test-injected transport
    with the same call shape. With verify_bytes, the landed blob's size is
    re-read and must equal the local file's — a short/failed upload refuses
    the run rather than finalizing a truncated object."""
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
    blob.upload_from_filename(str(local_path))
    if verify_bytes is not None:
        blob.reload()
        if blob.size != verify_bytes:
            raise RuntimeError(
                f"uploaded object gs://{bucket_name}/{dest} has size "
                f"{blob.size} != local {verify_bytes} — upload verification "
                "failed; refusing to finalize a truncated object")
    return f"gs://{bucket_name}/{dest}"


def _run(argv: list[str]) -> int:
    # amendment 3: the command line is logged with the DSN redacted, always.
    print("+ " + " ".join(redact_argv(argv)), flush=True)
    return subprocess.run(argv).returncode


def main(argv: list[str] | None = None, *, gcs_client=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
                             "attempt stages under a FRESH <workdir>/<run_id>/ "
                             "— a pre-existing non-empty run directory "
                             "refuses the run")
    parser.add_argument("--gcs-prefix", default=None,
                        help="gs://<bucket>/<prefix> for the per-body NDJSON "
                             "uploads; absent = logged no-op (local rehearsal, "
                             "objects stay in the run directory)")
    parser.add_argument("--delta-report", default=None,
                        help="§4.11 factor-level delta report vs '3.0', "
                             "forwarded to the candidate build (7.C: required "
                             "at tranche time)")
    parser.add_argument("--evidence", action="store_true")
    args = parser.parse_args(argv)

    # ── Guards (ADK-0027/0028/0029 + amendment 4) — before ANY filesystem or
    # subprocess work.
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

    # ── Fresh per-attempt staging (amendment 5).
    run_id = f"pravaha-a25-century-{int(time.time())}"
    workdir = Path(args.workdir
                   or f"century_run_{args.chart_id}_{args.generation}")
    run_dir = workdir / run_id
    if run_dir.exists() and any(run_dir.iterdir()):
        print(f"REFUSED (retry safety): run directory {run_dir} already "
              "exists and is not empty — every attempt stages under a FRESH "
              "run directory/object prefix; reusing one would mix attempts' "
              "appended streams.", file=sys.stderr)
        return 3
    episodes_dir = run_dir / "episodes"
    coverage_dir = run_dir / "coverage"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    coverage_dir.mkdir(parents=True, exist_ok=True)
    gcs_run_prefix = (f"{args.gcs_prefix.rstrip('/')}/{run_id}"
                      if args.gcs_prefix else None)

    chain_report: dict = {
        "driver": "century_run",
        "spec": "CENTURY_CLOUD_RUN_JOB_SPEC_v1_0",
        "chart_id": args.chart_id, "generation": args.generation,
        "horizon": f"[{args.horizon_start},{args.horizon_end})",
        "run_id": run_id,
        "run_dir": str(run_dir), "gcs_run_prefix": gcs_run_prefix,
        "bodies": list(PERSISTED_BODIES),
        "steps": [], "gcs_uploads": [],
    }

    def _abort(msg: str, rc: int) -> int:
        print(redact_text(msg), file=sys.stderr)
        print(json.dumps(chain_report, indent=2, default=str))
        return rc

    def _step(name: str, argv: list[str]) -> int:
        rc = _run(argv)
        chain_report["steps"].append({"step": name, "exit": rc})
        return rc

    common = ["--dsn", args.dsn, "--chart-id", args.chart_id,
              "--generation", args.generation,
              "--horizon-start", args.horizon_start,
              "--horizon-end", args.horizon_end]
    if args.evidence:
        common.append("--evidence")

    # 1. per-body enumeration, streaming NDJSON out (spec §2.2); 2. upload +
    #    free the local object right after each body (bounded tmpfs).
    objects: dict[str, dict] = {}
    for body in PERSISTED_BODIES:
        ndjson = episodes_dir / f"{body}.ndjson"
        step_argv = [sys.executable, str(STEP06), *common,
                     "--orb-deg", str(args.orb_deg),
                     "--bodies", body,
                     "--episodes-ndjson-out", str(ndjson),
                     "--coverage-out", str(coverage_dir / f"{body}.json")]
        if args.ephe_path:
            step_argv += ["--ephe-path", args.ephe_path]
        rc = _step(f"step06_enumerate_episodes[{body}]", step_argv)
        if rc != 0:
            return _abort(f"century_run aborted: enumeration of {body} exited "
                          f"{rc} — no input manifest is finalized and no "
                          "candidate build is attempted (§N.8)", rc)
        stats = _object_stats(ndjson)
        entry = {**stats, "run_id": run_id}
        dropped_refs = Path(str(ndjson) + ".dropped_refs.json")
        if gcs_run_prefix:
            try:
                entry["uri"] = upload_file_to_gcs(
                    gcs_run_prefix, ndjson, f"episodes/{body}.ndjson",
                    gcs_client=gcs_client, verify_bytes=stats["bytes"])
                chain_report["gcs_uploads"].append(entry["uri"])
                if dropped_refs.exists():
                    refs_uri = upload_file_to_gcs(
                        gcs_run_prefix, dropped_refs,
                        f"episodes/{body}.ndjson.dropped_refs.json",
                        gcs_client=gcs_client)
                    entry["dropped_refs_uri"] = refs_uri
                    chain_report["gcs_uploads"].append(refs_uri)
            except Exception as exc:
                return _abort(f"century_run aborted: GCS upload of {body} "
                              f"failed: {exc}", 3)
            # /tmp is RAM-backed tmpfs (F-185): the local per-body files are
            # deleted once the verified upload lands — nothing century-scale
            # is retained locally.
            ndjson.unlink()
            if dropped_refs.exists():
                dropped_refs.unlink()
        else:
            entry["uri"] = str(ndjson)
            if dropped_refs.exists():
                entry["dropped_refs_uri"] = str(dropped_refs)
            msg = (f"GCS upload SKIPPED (no --gcs-prefix): {ndjson} stays in "
                   "the run directory — local rehearsal shape")
            print(msg, flush=True)
            chain_report["gcs_uploads"].append(msg)
        objects[body] = entry

    # 3. merge coverage (sorted by partition_key — the monolithic order,
    #    amendment 6) and finalize the input manifest.
    coverage: list[dict] = []
    for body in PERSISTED_BODIES:
        coverage.extend(json.loads(
            (coverage_dir / f"{body}.json").read_text()))
    coverage.sort(key=lambda c: (c["partition_kind"], c["partition_key"]))
    merged_coverage = run_dir / "coverage.json"
    merged_coverage.write_text(json.dumps(coverage, indent=2, default=str) + "\n")
    cov_entry = {"uri": str(merged_coverage),
                 "sha256": coverage_binding(coverage),
                 "partitions": len(coverage)}
    if gcs_run_prefix:
        try:
            cov_entry["uri"] = upload_file_to_gcs(
                gcs_run_prefix, merged_coverage, "coverage.json",
                gcs_client=gcs_client)
        except Exception as exc:
            return _abort(f"century_run aborted: coverage upload failed: "
                          f"{exc}", 3)

    horizon_text = f"[{args.horizon_start},{args.horizon_end})"
    manifest = {
        "artifact": "CENTURY_INPUT_MANIFEST", "version": "1.0",
        "finalized": True,
        "run_id": run_id,
        "chart_id": args.chart_id, "generation": args.generation,
        "horizon": horizon_text,
        "bodies": list(PERSISTED_BODIES),
        "objects": objects,
        "coverage": cov_entry,
        "input_snapshot": {
            "spec": "CENTURY_CLOUD_RUN_JOB_SPEC_v1_0",
            "orb_deg": args.orb_deg,
            "ephe_path": args.ephe_path,
            "delta_report": args.delta_report,
        },
    }
    manifest_path = run_dir / "input_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n")
    if gcs_run_prefix:
        try:
            upload_file_to_gcs(gcs_run_prefix, manifest_path,
                               "input_manifest.json", gcs_client=gcs_client)
        except Exception as exc:
            return _abort(f"century_run aborted: manifest upload failed: "
                          f"{exc}", 3)
    chain_report["input_manifest"] = str(manifest_path)

    # 4. ONE candidate build from the finalized stream (spec §2.3): bounded
    #    streamed k-way merge, single transaction, manifest verified before
    #    any success (§N.8).
    build_argv = [sys.executable, str(STEP06_BUILD), *common,
                  "--orb-deg", str(args.orb_deg),
                  "--input-manifest", str(manifest_path)]
    if args.delta_report:
        build_argv += ["--delta-report", args.delta_report]
    rc = _step("step06_candidate_build", build_argv)
    if rc != 0:
        return _abort(f"century_run aborted: candidate build exited {rc}", rc)

    # 5. class context → windows projection → the delta report (spec §3).
    class_context = run_dir / "class_context.json"
    rc = _step("step06a_class_context",
               [sys.executable, str(STEP06A), "--dsn", args.dsn,
                "--chart-id", args.chart_id, "--generation", args.generation,
                "--out", str(class_context)]
               + (["--evidence"] if args.evidence else []))
    if rc != 0:
        return _abort(f"century_run aborted: class context exited {rc}", rc)

    delta_report_out = run_dir / "windows_delta_report.md"
    rc = _step("step06b_windows_projection",
               [sys.executable, str(STEP06B), *common,
                "--orb-deg", str(args.orb_deg),
                "--class-context-json", str(class_context),
                "--delta-report-out", str(delta_report_out)])
    if rc != 0:
        return _abort(f"century_run aborted: windows projection exited {rc}",
                      rc)

    chain_report["delta_report"] = str(delta_report_out)
    chain_report["status"] = "COMPLETE"
    print(json.dumps(chain_report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
