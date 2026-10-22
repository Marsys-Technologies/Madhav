#!/usr/bin/env python3
"""Read-only IAM EVIDENCE for the executor kind `iam_readback` (ruling of the owner surrogate madhav-44, item iam_readback; receipts for J-4c-a55m acts 12-14
= OWNER_GUIDE_v2 steps 10, 8, 7, and for the seal controller's steps 11-14).

The executor runs this for the fixed, reviewed, non-production, read-only kind `iam_readback`. The request names ONE probe from a fixed list and the
arguments that probe needs, nothing else (argparse with abbreviations off; any other argument exits 2 before a cloud call):

  --probe logging_view               --view <name>                       the narrow log view <name> of bucket _Default, location global
        gcloud logging views describe <name> --bucket=_Default --location=global --project=madhav-astrology --format=json
        gcloud logging views get-iam-policy <name> --bucket=_Default --location=global --project=madhav-astrology --format=json
  --probe run_job_iam                --job <name>                        the Cloud Run job <name> in asia-south1
        gcloud run jobs get-iam-policy <name> --region=asia-south1 --project=madhav-astrology --format=json
  --probe project_iam_member_role    --member <serviceAccount:...> --role <role>
        gcloud projects get-iam-policy madhav-astrology --format=json     (filtered in process to ONE member and ONE role; no other member is printed)
  --probe secret_version_exists      --secret <name>                     one of SECRETS (the sealer credential secret `gochara-sealer-db-url`), METADATA ONLY (SR-A55J-GAPS C7)
        gcloud secrets describe <name> --project=madhav-astrology --format=json
        gcloud secrets versions list <name> --project=madhav-astrology --format=json

The project is the constant PROJECT below; no argument names a project, a region, a bucket or a location. CALL_SHAPES is the whole list of command shapes,
and every command is built from it and checked (verb in READ_VERBS, every flag in FLAGS, the exact word layout) BEFORE the runner sees it, so this file can
only ever run `describe`, `get-iam-policy` or (for the secret's version list) `list`: a write verb (`add-iam-policy-binding`, `set-iam-policy`, ...) and above all `versions access` (the payload of a secret), an extra flag (`--impersonate-service-account`)
or a second resource is refused, not run.

Output: ONE line, a `ky.iam_readback_probe/1` JSON record (the executor receipt wraps it with the request digest, exit status and output digest):

  logging_view:               {schema, status: MEASURED, probe, measured_at, project, view: {name, bucket, location, filter}, bindings: [{role, members: [...]}]}
  run_job_iam:                {schema, status: MEASURED, probe, measured_at, project, job: {name, region}, bindings: [{role, members: [...]}]}
  project_iam_member_role:    {schema, status: MEASURED, probe, measured_at, project, member, role, held: true|false, bindings: [{role, members: [member]}] | []}
  secret_version_exists:      {schema, status: MEASURED, probe, measured_at, project, secret: {name, exists: true, create_time, labels, replication}, versions: [{version, state, create_time}]}
                              | {..., secret: {name, exists: false}, versions: []}      (only when gcloud answers NOT_FOUND; any other failure REFUSES)

`bindings` is normalised: sorted by role, members de-duplicated and sorted. (Distinct from `ky.iam_readback/1`, the no-argument four-call record of the sibling kind
`iam_policy_readback`, which the pre-century assembler judges; this record is never a substitute for it.) This file JUDGES nothing: the pass condition of an
act (exactly one binding, the member, the role) stays with whoever consumes the receipt.

Honest nulls (CLAUDE.md §N.7.6 / §N.8): a field a response does not carry is never filled in. A response that cannot be read as the thing it claims to be (a
view of another name, a missing or non-text filter, a binding with a field this reader does not know — notably a `condition`, which would make the grant
something other than unconditional —, a role or member that is not text, the same role twice, a policy field it does not know) REFUSES the whole record: status
REFUSED, exit 1, so a partial record can never be mistaken for evidence. A policy with no `bindings` key is the empty policy (gcloud omits the key when there are
none): a measured zero, not a refusal. For the project probe, `held` is true only for an UNCONDITIONAL binding of the role that lists the member; when the member
appears only in a conditional binding of that role the record REFUSES (a conditional grant is not the grant asked about).
Secret probe: the record never carries a payload, a checksum or an annotation; it is the secret's name, create time, labels and replication and, per version, the
number, state (ENABLED / DISABLED / DESTROYED) and create time, sorted by version number. There is NO `access` verb anywhere in this file (READ_VERBS has none; a
word `access` in any command is refused as well). `exists: false` is recorded only when gcloud's answer says NOT_FOUND (and not PERMISSION_DENIED): a measured absence;
every other failure is a REFUSED record, because an unreadable secret is not an absent one. The stderr is read for that one keyword and never relayed.
Credentials: this script never reads, prints or passes one. `gcloud` uses its own stored identity in the executor's allow-listed environment; the child's stderr is
never relayed (it may name an identity), only its exit status is. Members: the view's and the job's own policies are printed in full (the act judgment is on them);
the project policy is printed only as the one member the request named, and that member must be a service account of this project (never a person).
Standard library only: the executor copies this single file out of origin/main and runs it, so it cannot import its siblings."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys

SCHEMA = "ky.iam_readback_probe/1"
PROJECT = "madhav-astrology"
REGION = "asia-south1"
BUCKET = "_Default"
LOCATION = "global"
PROBES = ("logging_view", "run_job_iam", "project_iam_member_role", "secret_version_exists")
REQUIRED_ARGS = {"logging_view": ("view",), "run_job_iam": ("job",), "project_iam_member_role": ("member", "role"), "secret_version_exists": ("secret",)}
SECRETS = ("gochara-sealer-db-url",)                                     # the allow-list of secrets: the sealer credential secret (gochara-provision-roles.sh SEALER_SECRET; gochara-seal-approved.yml)
VIEW_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,62}")                           # a Cloud Logging view id (letters, digits, underscore; never starts with '-')
JOB_NAME_RE = re.compile(r"[a-z][a-z0-9-]{0,48}[a-z0-9]")                    # a Cloud Run job id (lower-case, digits, hyphen)
MEMBER_RE = re.compile(r"serviceAccount:[a-z][a-z0-9-]{4,28}[a-z0-9]@" + re.escape(PROJECT) + r"\.iam\.gserviceaccount\.com")   # a service account OF THIS PROJECT
ROLE_RE = re.compile(r"(?:roles/[A-Za-z0-9_.]+|projects/" + re.escape(PROJECT) + r"/roles/[A-Za-z0-9_.]+)")
SECRET_KEYS = frozenset({"name", "createTime", "labels", "replication", "etag", "annotations", "topics", "rotation", "expireTime", "ttl", "versionAliases",
                         "versionDestroyTtl", "customerManagedEncryption"})   # the fields of the Secret resource; none of them is the payload
SECRET_VERSION_KEYS = frozenset({"name", "state", "createTime", "destroyTime", "etag", "replicationStatus", "clientSpecifiedPayloadChecksum", "scheduledDestroyTime",
                                 "customerManagedEncryption"})                # the fields of a SecretVersion resource; the payload is a different resource (`access`)
VERSION_STATES = frozenset({"ENABLED", "DISABLED", "DESTROYED"})
SECRET_NAME_RE = re.compile(r"projects/[0-9]+/secrets/([A-Za-z0-9_-]{1,255})")
SECRET_VERSION_NAME_RE = re.compile(r"projects/[0-9]+/secrets/([A-Za-z0-9_-]{1,255})/versions/([0-9]+)")
VIEW_KEYS = frozenset({"name", "filter", "description", "createTime", "updateTime"})   # the fields of the LogView resource
POLICY_KEYS = frozenset({"bindings", "etag", "version", "auditConfigs"})                # the fields of an IAM Policy resource
BINDING_KEYS = frozenset({"role", "members"})                            # `condition` is deliberately absent: a conditional binding is not the grant it names
GCLOUD_TIMEOUT_S = 120
READ_VERBS = frozenset({"describe", "get-iam-policy", "list"})           # the only gcloud verbs this file may run (`list` only in the secret versions shape below)
NEVER_WORDS = frozenset({"access"})                                      # a command word that is refused whatever the verb: the payload of a secret
FLAGS = frozenset({"--bucket", "--location", "--region", "--project", "--format"})   # the only flags a call may carry; each takes its value as `--flag=value`

# The whole list of command shapes: (command words, verb index in them, flags template). `{x}` is replaced by an already-validated argument or constant.
_LOG = (f"--bucket={BUCKET}", f"--location={LOCATION}", f"--project={PROJECT}", "--format=json")
CALL_SHAPES = {
    "view": ("gcloud", "logging", "views", "describe", "{view}", *_LOG),
    "view_policy": ("gcloud", "logging", "views", "get-iam-policy", "{view}", *_LOG),
    "job_policy": ("gcloud", "run", "jobs", "get-iam-policy", "{job}", f"--region={REGION}", f"--project={PROJECT}", "--format=json"),
    "project_policy": ("gcloud", "projects", "get-iam-policy", PROJECT, "--format=json"),
    "secret": ("gcloud", "secrets", "describe", "{secret}", f"--project={PROJECT}", "--format=json"),
    "secret_versions": ("gcloud", "secrets", "versions", "list", "{secret}", f"--project={PROJECT}", "--format=json"),
}
CALLS_OF = {"logging_view": ("view", "view_policy"), "run_job_iam": ("job_policy",), "project_iam_member_role": ("project_policy",), "secret_version_exists": ("secret", "secret_versions")}


class Refused(RuntimeError):
    pass


def default_runner(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=GCLOUD_TIMEOUT_S, check=False, stdin=subprocess.DEVNULL)


def read_verb(argv) -> str | None:
    """The gcloud verb of a call: the last command word before the resource name (flags are `--...`). None when there is none."""
    words = [a for a in argv[1:] if not a.startswith("--")]
    return words[-2] if len(words) >= 2 else None


def check_read_only(argv) -> None:
    """Refuse (before any runner) a command that is not a plain read: gcloud first, the verb a read, only the fixed flags, each as `--flag=value`."""
    if not argv or argv[0] != "gcloud":
        raise Refused("not a gcloud command")
    verb = read_verb(argv)
    if verb not in READ_VERBS:
        raise Refused(f"the gcloud verb {verb!r} is not a read")
    if any(word in NEVER_WORDS for word in argv[1:]):
        raise Refused("the command word 'access' (a secret's payload) is never run")
    for word in argv[1:]:
        if word.startswith("--") and word.split("=", 1)[0] not in FLAGS:
            raise Refused(f"the flag {word.split('=', 1)[0]!r} is not one of the fixed flags")
        if word.startswith("--") and "=" not in word:
            raise Refused(f"the flag {word!r} is not in --flag=value form")
    if len([a for a in argv[1:] if not a.startswith("--")]) not in (3, 4):    # group(s) + verb + one resource: never a second resource or member
        raise Refused("unexpected command shape")


def build_command(call: str, args: dict) -> list[str]:
    """One fixed command from CALL_SHAPES with the validated arguments filled in. An unknown call name, or a command that is not a plain read, is refused."""
    shape = CALL_SHAPES.get(call)
    if shape is None:
        raise Refused(f"{call}: not one of the fixed calls")
    argv = [w.format(**args) if "{" in w else w for w in shape]
    check_read_only(argv)
    return argv


def validate_args(probe: str, args: dict) -> dict:
    """The arguments of a probe against the fixed allow-list: exactly the probe's own, each in its closed shape. Raises Refused, which the CLI turns into exit 2."""
    if probe not in PROBES:
        raise Refused(f"probe {probe!r} is not one of {list(PROBES)}")
    given = {k: v for k, v in args.items() if v is not None}
    if sorted(given) != sorted(REQUIRED_ARGS[probe]):
        raise Refused(f"probe {probe} takes exactly {list(REQUIRED_ARGS[probe])}")
    shapes = {"view": VIEW_NAME_RE, "job": JOB_NAME_RE, "member": MEMBER_RE, "role": ROLE_RE}
    for key, value in given.items():
        if key == "secret":
            if value not in SECRETS:
                raise Refused(f"the secret argument is not one of {list(SECRETS)}")
        elif not isinstance(value, str) or not shapes[key].fullmatch(value):
            raise Refused(f"the {key} argument is not an allowed name")
    return given


def gcloud_json(argv: list[str], runner, label: str, expect=dict, not_found_ok: bool = False):
    """One built command. It is checked read-only again here (a template edited in place is caught) BEFORE the runner sees it. The child's stderr is never relayed.
    `expect` is the JSON type the answer must have (the version list is a list). With `not_found_ok`, a failed call whose stderr says NOT_FOUND (and not PERMISSION_DENIED)
    returns None: the measured absence of the resource."""
    try:
        check_read_only(argv)
    except Refused as exc:
        raise Refused(f"{label}: {exc}") from None
    try:
        result = runner(list(argv))
    except (OSError, subprocess.SubprocessError):
        raise Refused(f"{label}: gcloud could not be run or timed out") from None
    if result.returncode:
        err = result.stderr if isinstance(result.stderr, str) else ""
        if not_found_ok and "NOT_FOUND" in err and "PERMISSION_DENIED" not in err:
            return None
        raise Refused(f"{label}: gcloud exited {result.returncode}")
    try:
        value = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise Refused(f"{label}: gcloud output is not JSON") from None
    if not isinstance(value, expect):
        raise Refused(f"{label}: gcloud output is not a JSON {'object' if expect is dict else 'list'}")
    return value


def _check_policy_keys(policy: dict, label: str) -> list:
    unknown = sorted(set(policy) - POLICY_KEYS)
    if unknown:
        raise Refused(f"{label}: the policy carries a field this reader does not know ({unknown[0]!r})")
    raw = policy.get("bindings", [])
    if not isinstance(raw, list):
        raise Refused(f"{label}: bindings is not a list")
    return raw


def _members(binding: dict, role: str, label: str) -> list[str]:
    members = binding.get("members")
    if not isinstance(members, list) or not members or any(not isinstance(m, str) or not m or m != m.strip() or " " in m for m in members):
        raise Refused(f"{label}: the members of {role} are missing or not text")
    return members


def read_bindings(policy: dict, label: str) -> list[dict]:
    """[{role, members}] sorted by role, members de-duplicated and sorted. An unknown policy field, an unknown binding field or a malformed role or member REFUSES."""
    out, seen = [], set()
    for binding in _check_policy_keys(policy, label):
        if not isinstance(binding, dict):
            raise Refused(f"{label}: a binding is not an object")
        unknown = sorted(set(binding) - BINDING_KEYS)
        if unknown:
            raise Refused(f"{label}: a binding carries a field this reader does not know ({unknown[0]!r}); a conditional grant is not judged here")
        role = binding.get("role")
        if not isinstance(role, str) or not ROLE_RE.fullmatch(role):
            raise Refused(f"{label}: a binding's role is missing or not a role name")
        members = _members(binding, role, label)
        if role in seen:
            raise Refused(f"{label}: {role} is bound twice")
        seen.add(role)
        out.append({"role": role, "members": sorted(set(members))})
    return sorted(out, key=lambda b: b["role"])


def member_role_held(policy: dict, member: str, role: str, label: str) -> bool:
    """True when an UNCONDITIONAL binding of `role` lists `member`; False when none does. Only bindings of `role` are read in depth (a project policy carries
    many unrelated, often conditional, bindings that are neither judged nor printed). The member appearing only in a conditional binding of `role` REFUSES."""
    held, conditional = False, False
    for binding in _check_policy_keys(policy, label):
        if not isinstance(binding, dict) or not isinstance(binding.get("role"), str):
            raise Refused(f"{label}: a binding is not an object with a role")
        if binding["role"] != role:
            continue
        members = _members(binding, role, label)
        if member not in members:
            continue
        if set(binding) - BINDING_KEYS:
            if set(binding) - BINDING_KEYS - {"condition"}:
                raise Refused(f"{label}: a binding of {role} carries a field this reader does not know")
            conditional = True
        else:
            held = True
    if conditional and not held:
        raise Refused(f"{label}: {member} holds {role} only through a conditional binding; a conditional grant is not judged here")
    return held


def read_secret(secret: dict, name: str) -> dict:
    """{name, exists, create_time, labels, replication} of the Secret resource, nothing else (no annotation, topic or rotation is printed)."""
    unknown = sorted(set(secret) - SECRET_KEYS)
    if unknown:
        raise Refused(f"secret: the response carries a field this reader does not know ({unknown[0]!r})")
    found = SECRET_NAME_RE.fullmatch(secret["name"]) if isinstance(secret.get("name"), str) else None
    if not found or found.group(1) != name:
        raise Refused(f"secret: the response is not for the secret {name}")
    create_time, labels, replication = secret.get("createTime"), secret.get("labels", {}), secret.get("replication")
    if not isinstance(create_time, str) or not create_time:
        raise Refused("secret: createTime is missing or not text")
    if not isinstance(labels, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in labels.items()):
        raise Refused("secret: labels are not a text map")
    if not isinstance(replication, dict) or not replication:
        raise Refused("secret: replication is missing or not an object")
    return {"name": name, "exists": True, "create_time": create_time, "labels": dict(sorted(labels.items())), "replication": replication}


def read_versions(versions: list, name: str) -> list[dict]:
    """[{version, state, create_time}] sorted by version number, only the three fields: never a payload, checksum or replication status. An unknown field, a state outside
    ENABLED / DISABLED / DESTROYED, a version of another secret or the same version twice REFUSES."""
    out, seen = [], set()
    for item in versions:
        if not isinstance(item, dict):
            raise Refused("secret_versions: a version is not an object")
        unknown = sorted(set(item) - SECRET_VERSION_KEYS)
        if unknown:
            raise Refused(f"secret_versions: a version carries a field this reader does not know ({unknown[0]!r})")
        found = SECRET_VERSION_NAME_RE.fullmatch(item["name"]) if isinstance(item.get("name"), str) else None
        if not found or found.group(1) != name:
            raise Refused(f"secret_versions: a version is not of the secret {name}")
        number = int(found.group(2))
        if number in seen:
            raise Refused(f"secret_versions: version {number} is listed twice")
        seen.add(number)
        if item.get("state") not in VERSION_STATES:
            raise Refused(f"secret_versions: the state of version {number} is missing or not ENABLED / DISABLED / DESTROYED")
        if not isinstance(item.get("createTime"), str) or not item["createTime"]:
            raise Refused(f"secret_versions: the createTime of version {number} is missing or not text")
        out.append({"version": number, "state": item["state"], "create_time": item["createTime"]})
    return sorted(out, key=lambda v: v["version"])


def measure(probe: str, args: dict, runner=default_runner, clock=lambda: dt.datetime.now(dt.timezone.utc)) -> dict:
    args = validate_args(probe, args)
    base = {"schema": SCHEMA, "status": "MEASURED", "probe": probe, "measured_at": clock().strftime("%Y-%m-%dT%H:%M:%SZ"), "project": PROJECT}
    if probe == "logging_view":
        name = args["view"]
        view = gcloud_json(build_command("view", args), runner, "view")
        unknown = sorted(set(view) - VIEW_KEYS)
        if unknown:
            raise Refused(f"view: the response carries a field this reader does not know ({unknown[0]!r})")
        if view.get("name") != f"projects/{PROJECT}/locations/{LOCATION}/buckets/{BUCKET}/views/{name}":
            raise Refused(f"view: the response is not for the {name} view of {BUCKET}/{LOCATION}")
        view_filter = view.get("filter")
        if not isinstance(view_filter, str) or not view_filter:
            raise Refused("view: the filter is missing or not text")
        bindings = read_bindings(gcloud_json(build_command("view_policy", args), runner, "view_policy"), "view_policy")
        return {**base, "view": {"name": name, "bucket": BUCKET, "location": LOCATION, "filter": view_filter}, "bindings": bindings}
    if probe == "run_job_iam":
        bindings = read_bindings(gcloud_json(build_command("job_policy", args), runner, "job_policy"), "job_policy")
        return {**base, "job": {"name": args["job"], "region": REGION}, "bindings": bindings}
    if probe == "secret_version_exists":
        name = args["secret"]
        secret = gcloud_json(build_command("secret", args), runner, "secret", not_found_ok=True)
        if secret is None:
            return {**base, "secret": {"name": name, "exists": False}, "versions": []}
        described = read_secret(secret, name)
        versions = read_versions(gcloud_json(build_command("secret_versions", args), runner, "secret_versions", expect=list), name)
        return {**base, "secret": described, "versions": versions}
    member, role = args["member"], args["role"]
    held = member_role_held(gcloud_json(build_command("project_policy", args), runner, "project_policy"), member, role, "project_policy")
    return {**base, "member": member, "role": role, "held": held, "bindings": [{"role": role, "members": [member]}] if held else []}


def cli(argv=None, runner=default_runner) -> int:
    parser = argparse.ArgumentParser(description="Read-only IAM evidence for one fixed probe (no free-form command).", allow_abbrev=False)
    parser.add_argument("--probe", required=True, choices=PROBES)
    for key in ("view", "job", "member", "role", "secret"):
        parser.add_argument(f"--{key}")
    ns = parser.parse_args(argv)                                         # an unknown flag, a missing --probe or a bad probe exits 2 before a cloud call
    args = {k: getattr(ns, k) for k in ("view", "job", "member", "role", "secret")}
    try:
        validate_args(ns.probe, args)
    except Refused as exc:
        parser.error(str(exc))                                           # exit 2, before any call
    try:
        record, code = measure(ns.probe, args, runner), 0
    except Refused as exc:
        record, code = {"schema": SCHEMA, "status": "REFUSED", "probe": ns.probe, "reason": str(exc)}, 1
    print(json.dumps(record, sort_keys=True, separators=(",", ":")), flush=True)
    return code


if __name__ == "__main__":
    sys.exit(cli())
