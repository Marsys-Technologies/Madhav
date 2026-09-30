#!/usr/bin/env python3
"""century_run.py — Pravāha A2.5 century execution-chain driver (chart 482012f1,
generation '4.1'), implementing CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 §3.

Chain (per A2.5 run, one Cloud Run job execution with a container override):

  1. loop PERSISTED_BODIES (the eight non-Moon grahas, imported from
     step06_enumerate_episodes — never restated here): step06 enumeration with
     --bodies <body> --episodes-ndjson-out <workdir>/episodes/<body>.ndjson
     (streaming per-body append; per-body peak memory only, spec §2.2) and
     --coverage-out <workdir>/coverage/<body>.json;
  2. ONE candidate build (step06_candidate_build.py) from the concatenated
     NDJSON stream (--episodes-ndjson '<workdir>/episodes/*.ndjson') plus the
     merged per-body coverage list — single transaction, the honest shape
     (spec §2: 8 partial DB-direct builds were REJECTED);
  3. step06a_class_context.py → step06b_windows_projection.py with
     --delta-report-out (the report).

Exit codes propagate per step, unchanged: 7 = §12.9 stale-overlay refusal,
6 = publish refusal, 5 = ADK-0020/0021/0022 dedupe refusal, 4 = production
guard (inherited from common.connect), 3 = cannot proceed. The first nonzero
step exit aborts the chain with that code.

GUARD (ADK-0028: no local century enumeration, ever). This driver REFUSES to
run unless BOTH hold:
  * env PRAVAHA_CENTURY_RUN_AUTHORIZED=1 — the marker the Cloud Run job's
    container override sets (spec §3); absent anywhere else, so a local
    invocation exits 3 before any subprocess starts;
  * the requested horizon IS the pinned century window
    [1984-02-05T00:00:00+00:00, 2084-02-05T00:00:00+00:00) — nothing else is
    a century run this driver will execute.
Decade-scale rehearsals keep using step06_enumerate_episodes.py directly;
this driver is the century shape only.

GCS upload (spec §2.2): with --gcs-prefix gs://<bucket>/<prefix>, each body's
NDJSON is uploaded to <prefix>/<body>.ndjson right after that body's
enumeration (google-cloud-storage, already in the sidecar image; imported
lazily so local rehearsals never require it). The prefix's bucket is used
AS-IS via client.bucket(...) — buckets are NEVER created here (bucket choice
and grants are native infra, spec pre-flight checklist). Without
--gcs-prefix the upload is a logged no-op and the run stays local to
--workdir.

Resume rule (spec §3): a failed execution leaves a `candidate` manifest at
worst; re-run is a fresh build of the same generation label — candidate rows
are replaced, never edited in place (N-7). Use a FRESH --workdir per run (the
NDJSON files are appended to, never truncated).

Usage (inside the Cloud Run job only):
    PRAVAHA_CENTURY_RUN_AUTHORIZED=1 \
    python3 scripts/kala_gochara_cutover/century_run.py \
        --dsn postgresql://... --chart-id 482012f1-... --generation 4.1 \
        [--workdir /tmp/century] [--gcs-prefix gs://<build-artifacts>/kala_gochara/482012f1/4.1/episodes] \
        [--orb-deg 5.0] [--ephe-path ...] [--delta-report path] [--evidence]

Exit codes: 0 chain complete; 3 guard refusal / cannot proceed; otherwise the
failing step's exit code propagates verbatim.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from step06_enumerate_episodes import PERSISTED_BODIES  # noqa: E402

# The pinned century window (CENTURY_CLOUD_RUN_JOB_SPEC_v1_0 header / f0p2
# evidence step 1; no narrowing ruling exists).
CENTURY_HORIZON_START = "1984-02-05T00:00:00+00:00"
CENTURY_HORIZON_END = "2084-02-05T00:00:00+00:00"

AUTHORIZATION_ENV = "PRAVAHA_CENTURY_RUN_AUTHORIZED"

STEP06 = HERE / "step06_enumerate_episodes.py"
STEP06_BUILD = HERE / "step06_candidate_build.py"
STEP06A = HERE / "step06a_class_context.py"
STEP06B = HERE / "step06b_windows_projection.py"


def upload_ndjson_to_gcs(gcs_prefix: str | None, local_path: Path,
                         blob_name: str) -> str:
    """Upload one per-body NDJSON file under gs://<bucket>/<prefix>/<blob_name>.

    No-op (with a printed disclosure) when gcs_prefix is None — a local
    rehearsal writes only the local workdir. google-cloud-storage is imported
    lazily: it is present in the sidecar image (spec pre-flight precedent:
    madhav-marsys-sources) but a local rehearsal must not require it. The
    bucket is used as-is; this code NEVER creates buckets or grants (native
    infra, spec pre-flight checklist)."""
    if not gcs_prefix:
        return (f"GCS upload SKIPPED (no --gcs-prefix): {local_path} stays "
                "local — local rehearsal shape, nothing leaves the workdir")
    if not gcs_prefix.startswith("gs://"):
        raise ValueError(f"--gcs-prefix must be gs://<bucket>/<prefix>, got "
                         f"{gcs_prefix!r}")
    from google.cloud import storage  # lazy: sidecar image only

    bucket_name, _, prefix = gcs_prefix[5:].partition("/")
    dest = f"{prefix.rstrip('/')}/{blob_name}" if prefix else blob_name
    client = storage.Client()
    bucket = client.bucket(bucket_name)  # never create_bucket: native infra
    bucket.blob(dest).upload_from_filename(str(local_path))
    return f"uploaded {local_path} -> gs://{bucket_name}/{dest}"


def _run(argv: list[str]) -> int:
    print("+ " + " ".join(argv), flush=True)
    return subprocess.run(argv).returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", required=True)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default="4.1")
    parser.add_argument("--horizon-start", default=CENTURY_HORIZON_START)
    parser.add_argument("--horizon-end", default=CENTURY_HORIZON_END)
    parser.add_argument("--orb-deg", type=float, default=5.0)
    parser.add_argument("--ephe-path", default=None,
                        help="forwarded to step06 (its own default is the "
                             "pinned local set when omitted)")
    parser.add_argument("--workdir", default=None,
                        help="local streaming directory (default "
                             "./century_run_<chart-id>_<generation>); use a "
                             "FRESH directory per run — NDJSON is append-only")
    parser.add_argument("--gcs-prefix", default=None,
                        help="gs://<bucket>/<prefix> for the per-body NDJSON "
                             "uploads; absent = logged no-op (local rehearsal)")
    parser.add_argument("--delta-report", default=None,
                        help="§4.11 factor-level delta report vs '3.0', "
                             "forwarded to the candidate build (7.C: required "
                             "at tranche time)")
    parser.add_argument("--evidence", action="store_true")
    args = parser.parse_args(argv)

    # ADK-0028 guard — before ANY subprocess or DB touch.
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

    workdir = Path(args.workdir
                   or f"century_run_{args.chart_id}_{args.generation}")
    episodes_dir = workdir / "episodes"
    coverage_dir = workdir / "coverage"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    coverage_dir.mkdir(parents=True, exist_ok=True)

    chain_report: dict = {
        "driver": "century_run",
        "spec": "CENTURY_CLOUD_RUN_JOB_SPEC_v1_0",
        "chart_id": args.chart_id, "generation": args.generation,
        "horizon": f"[{args.horizon_start},{args.horizon_end})",
        "workdir": str(workdir), "gcs_prefix": args.gcs_prefix,
        "bodies": list(PERSISTED_BODIES),
        "steps": [], "gcs_uploads": [],
        "run_id": f"pravaha-a25-century-{int(time.time())}",
    }

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

    # 1. per-body enumeration, streaming NDJSON out (spec §2.2).
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
            print(f"century_run aborted: enumeration of {body} exited {rc}",
                  file=sys.stderr)
            print(json.dumps(chain_report, indent=2, default=str))
            return rc
        msg = upload_ndjson_to_gcs(args.gcs_prefix, ndjson, f"{body}.ndjson")
        print(msg, flush=True)
        chain_report["gcs_uploads"].append(msg)

    # 2. ONE candidate build from the concatenated stream (spec §2.3).
    coverage: list[dict] = []
    for body in PERSISTED_BODIES:
        coverage.extend(json.loads(
            (coverage_dir / f"{body}.json").read_text()))
    merged_coverage = workdir / "coverage.json"
    merged_coverage.write_text(json.dumps(coverage, indent=2, default=str) + "\n")
    build_argv = [sys.executable, str(STEP06_BUILD), *common,
                  "--orb-deg", str(args.orb_deg),
                  "--episodes-ndjson", str(episodes_dir / "*.ndjson"),
                  "--coverage-json", str(merged_coverage)]
    if args.delta_report:
        build_argv += ["--delta-report", args.delta_report]
    rc = _step("step06_candidate_build", build_argv)
    if rc != 0:
        print(f"century_run aborted: candidate build exited {rc}",
              file=sys.stderr)
        print(json.dumps(chain_report, indent=2, default=str))
        return rc

    # 3. class context → windows projection → the delta report (spec §3).
    class_context = workdir / "class_context.json"
    rc = _step("step06a_class_context",
               [sys.executable, str(STEP06A), "--dsn", args.dsn,
                "--chart-id", args.chart_id, "--generation", args.generation,
                "--out", str(class_context)]
               + (["--evidence"] if args.evidence else []))
    if rc != 0:
        print(f"century_run aborted: class context exited {rc}", file=sys.stderr)
        print(json.dumps(chain_report, indent=2, default=str))
        return rc

    delta_report_out = workdir / "windows_delta_report.md"
    rc = _step("step06b_windows_projection",
               [sys.executable, str(STEP06B), *common,
                "--orb-deg", str(args.orb_deg),
                "--class-context-json", str(class_context),
                "--delta-report-out", str(delta_report_out)])
    if rc != 0:
        print(f"century_run aborted: windows projection exited {rc}",
              file=sys.stderr)
        print(json.dumps(chain_report, indent=2, default=str))
        return rc

    chain_report["delta_report"] = str(delta_report_out)
    chain_report["status"] = "COMPLETE"
    print(json.dumps(chain_report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
