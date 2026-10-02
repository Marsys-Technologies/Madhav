#!/usr/bin/env python3
"""ONE strict validator of the verification job's TASK TEMPLATE — shared, byte for byte, by the job-definition readback (#2976, deployment time) and the executed-resource
check (#2975, run time) (Codex R14-3). A deployed definition proves nothing about a later execution, and an execution that is merely "close" to the definition proves nothing
about who ran it, so BOTH are judged by the same function against the same contract:

  image            == <repository>@<immutable sha256 digest> (a tag, another digest or another repository is refused)
  command          == `python -m pipeline.orchestrator.verification_job` — the builder's entry point is overridden, and an execution may not swap it back
  args             == exactly the expected list (the definition: none; an execution: exactly the arguments the sealing workflow passed)
  retries          == `maxRetries` PRESENT and == 0 — an ABSENT value is a refusal, never zero (Cloud Run's documented default is 3, and a retried task could produce a stale brief)
  environment      == exactly GOCHARA_RUNNER_COMMIT (the commit, a plain value), GOCHARA_RUNNER_IMAGE_DIGEST (the digest, a plain value) and GOCHARA_VERIFIER_DB_URL (a secret
                      reference to the verifier secret, no literal value) — an extra variable, a missing one, a literal secret or `envFrom` is refused
  credential       == no `volumes` (so no secret volume), no `volumeMounts`, no `envFrom`, no other container field that can carry a credential; the container and task carry ONLY the
  surfaces            fields this contract names (an unknown field is a refusal — fail closed; the first real execution is the proof of the shape, runbook act 6b)
  identity         == exactly the verifier's runtime service account
  one container    == no sidecar, no init container

RETRIES PRESENCE (Fable F-R15-3). The Cloud Run reference lists `maxRetries` under the union field `retries` in BOTH the v1 `TaskSpec` and the v2 `TaskTemplate` (default 3 when unset). A union (oneof) member carries PRESENCE, so an explicitly set 0 is serialized — but
that is the documentation's statement, not an observation of `gcloud` output (the first real describe is the proof). This contract therefore NEVER treats an absent value as zero: `validate_task` accepts an optional `v2_retries` — the value read from the v2 REST representation
(`jobs.get` → `template.template.maxRetries`; `executions.get` → `template.maxRetries`) via `retries_from_v2` — and the effective value is the v1 value if present, else the v2 value; if both are present they must agree; if NEITHER carries it the task is REFUSED (a real absence is the API default of 3).

It returns a list of problems (empty = conforms). The JSON shape is the documented Cloud Run TaskSpec; a mismatch of SHAPE is a refusal, never a pass."""
from __future__ import annotations

ENTRYPOINT = ["python", "-m", "pipeline.orchestrator.verification_job"]
ENV_COMMIT = "GOCHARA_RUNNER_COMMIT"
ENV_IMAGE = "GOCHARA_RUNNER_IMAGE_DIGEST"
ENV_SECRET = "GOCHARA_VERIFIER_DB_URL"
ENV_NAMES = {ENV_COMMIT, ENV_IMAGE, ENV_SECRET}
CONTAINER_FIELDS = {"name", "image", "command", "args", "env", "resources"}
TASK_FIELDS = {"containers", "serviceAccountName", "maxRetries", "timeoutSeconds", "executionEnvironment", "volumes"}


UNSET = object()


def retries_from_v2(doc, kind: str):
    """`maxRetries` read from the v2 REST representation: a job (`projects.locations.jobs.get`) carries it at `template.template.maxRetries`, an execution
    (`projects.locations.jobs.executions.get`) at `template.maxRetries`. Returns the integer, or None when the field is ABSENT (never defaulted)."""
    if not isinstance(doc, dict):
        return None
    t = doc.get("template")
    if kind == "job" and isinstance(t, dict):
        t = t.get("template")
    if not isinstance(t, dict):
        return None
    v = t.get("maxRetries")
    return v if (isinstance(v, int) and not isinstance(v, bool)) else None


def validate_task(task, *, image_repo: str, image_digest: str, service_account: str, runner_commit: str, secret_name: str, expected_args: list,
                  timeout_seconds: int | None = None, memory: str | None = None, cpu: str | None = None, v2_retries=UNSET) -> list[str]:
    bad: list[str] = []
    if not isinstance(task, dict):
        return ["the task template is not an object"]
    for k in sorted(set(task) - TASK_FIELDS):
        bad.append(f"unexpected task field {k!r}")
    if task.get("volumes"):
        bad.append("the task template declares volumes (a secret or other volume is a credential surface)")
    cs = task.get("containers")
    if not isinstance(cs, list) or len(cs) != 1 or not isinstance(cs[0], dict):
        return bad + [f"the task has {len(cs) if isinstance(cs, list) else 'no'} containers, not exactly one (no sidecar, no init container)"]
    c = cs[0]
    for k in sorted(set(c) - CONTAINER_FIELDS):
        bad.append(f"unexpected container field {k!r} (volumeMounts / envFrom / probes / ports are credential or behaviour surfaces this job does not use)")
    if c.get("image") != f"{image_repo}@{image_digest}":
        bad.append(f"image is {c.get('image')!r}, not {image_repo}@{image_digest}")
    if task.get("serviceAccountName") != service_account:
        bad.append(f"service account is {task.get('serviceAccountName')!r}, not {service_account!r}")
    if c.get("command") != ENTRYPOINT:
        bad.append(f"command is {c.get('command')!r}, not {ENTRYPOINT!r}")
    if list(c.get("args") or []) != list(expected_args):
        bad.append(f"args are {c.get('args')!r}, expected {list(expected_args)!r}")
    retries = task.get("maxRetries")
    if v2_retries is not UNSET and retries is not None and v2_retries is not None and retries != v2_retries:
        bad.append(f"maxRetries disagrees between the v1 ({retries!r}) and v2 ({v2_retries!r}) representations")
    effective = retries if retries is not None else (None if v2_retries is UNSET else v2_retries)
    if effective is None or isinstance(effective, bool) or effective != 0:
        bad.append(f"maxRetries is {effective!r} (v1: {retries!r}), expected a PRESENT 0 in a presence-bearing representation (an absent value is the API default of 3)")
    env = c.get("env")
    if not isinstance(env, list) or not all(isinstance(e, dict) for e in env):
        bad.append("env is not a list of objects")
        env = []
    names = [e.get("name") for e in env]
    if len(names) != len(set(names)) or set(names) != ENV_NAMES:
        bad.append(f"environment variables are {sorted(map(str, names))}, expected exactly {sorted(ENV_NAMES)} once each")
    else:
        by = {e["name"]: e for e in env}
        for name, want in ((ENV_COMMIT, runner_commit), (ENV_IMAGE, image_digest)):
            e = by[name]
            if e.get("value") != want or set(e) - {"name", "value"}:
                bad.append(f"{name} is not exactly the plain value {want!r}")
        e = by[ENV_SECRET]
        ref = (e.get("valueFrom") or {}).get("secretKeyRef") if isinstance(e.get("valueFrom"), dict) else None
        if "value" in e or not isinstance(ref, dict) or ref.get("name") != secret_name or set(e) - {"name", "valueFrom"} or set(e["valueFrom"]) != {"secretKeyRef"}:
            bad.append(f"{ENV_SECRET} is not exactly a reference to the secret {secret_name} (no literal value, no other source)")
    if timeout_seconds is not None and task.get("timeoutSeconds") != timeout_seconds:
        bad.append(f"timeoutSeconds is {task.get('timeoutSeconds')!r}, expected {timeout_seconds}")
    lim = (c.get("resources") or {}).get("limits") if isinstance(c.get("resources"), dict) else None
    if memory is not None and str((lim or {}).get("memory")) != memory:
        bad.append(f"memory limit is {(lim or {}).get('memory')!r}, expected {memory}")
    if cpu is not None and str((lim or {}).get("cpu")) != cpu:
        bad.append(f"cpu limit is {(lim or {}).get('cpu')!r}, expected {cpu}")
    return bad
