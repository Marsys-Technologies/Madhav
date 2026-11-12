#!/usr/bin/env python3
"""Generator and checker of fleet/century_contract.json, the century launch's declared facts (SR-EDGES-PROOF 2, SR-HORIZON-PUBLIC, SR-W34-LEASE).

Nothing in the contract is typed: every value is read from the source that owns it, and `--check` regenerates the file and compares it.
    horizon       start = DEFAULT_HORIZON[0] in ka_gochara_v5.py; end = the native's birth date (root CLAUDE.md §B) + 100 years. ISO 8601 UTC strings, half-open [start, end)
                  (SR-HORIZON-PUBLIC: both bounds are public, committed verbatim; SR-W34-LEASE: the carrier format is the writer's own printed form, never epoch integers)
    classes       the scored classes (gochara_rules.registry.ROW_MEMBERSHIP, the writer's SCORED_CLASSES rule) and the dispatch's `classes` selector
    policy        the contact-certification policy an unmarked (non-slice) run takes, read from the writer's own selection; the writer's config key names; final rules and
                  the in-build-verify deferral from the W3W4 pack's VERIFY_DEFERRAL.json carrier.args (SR-W3-SHAPE 3 / SR-W34-PREP-RULINGS 1) when --pack is given
    cap           the writer watchdog (migration 1395 SET writer_timeout_seconds)       timeout   the Cloud Run job task timeout (deploy.yml, the pipeline job's update step)
    image         the Cloud Run job, project, region, image repository and the writer-source digest the deployed image must carry (writer_runtime_support.get_writer_source_hash)
    + the pack-bound launch facts (generation, triggered_by, stored_scope, launch_args, output_tables, cancel_schema) that century/rebind_pins.py binds from this file.

The executor binds a century dispatch (and its dry run) to this file: the request carries `century_contract_sha256` and the executor refuses it unless it equals the sha256 of
the file's bytes at the request's reviewed_commit (executor.century_contract_problem). The sidecar import for the image digest is lazy: without the sidecar dependencies
`--write` and `--check` refuse (never skip) unless `--no-image` is given, which `--check` reports as a partial check.

    python3 century_contract.py --write --pack <W3W4 PACK dir>      regenerate the file
    python3 century_contract.py --check [--pack <PACK dir>]         exit 0 only when the committed file equals the generated one
Reads only; --write writes only the contract file. No network, no database, no git.
"""
from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import importlib.util
import json
import re
import shlex
import sys
import textwrap
from pathlib import Path

FLEET = Path(__file__).resolve().parent
REPO = FLEET.parents[3]
REL = "00_ARCHITECTURE/briefs/kalayantra/fleet/century_contract.json"
SCHEMA = "ky.century_contract/1"
ITEM = "J-4e"
RULINGS = ["SR-EDGES-PROOF 2", "SR-HORIZON-PUBLIC", "SR-W34-LEASE", "SR-W3-SHAPE 3", "SR-J3-CAP-LIVE"]
BIRTH_PATH = "CLAUDE.md"
HORIZON_YEARS = 100
WRITER = "platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py"
REGISTRY = "platform/python-sidecar/services/gochara_rules/registry.py"
CERTIFY = "platform/python-sidecar/services/gochara_kernel/contact_certify.py"
INPUT_VECTOR = "platform/python-sidecar/services/gochara_kernel/input_vector.py"
SHARED = "platform/scripts/v5_small_test_shared.py"
DISPATCH = "platform/scripts/dispatch_v5_century_job.py"
CANCEL = "00_ARCHITECTURE/briefs/kalayantra/fleet/century_cancel.py"
CAP_MIGRATION = "platform/migrations/1395_ka_gochara_v5_writer_timeout_72000.sql"
DEPLOY = ".github/workflows/deploy.yml"
PACK_FILE = "VERIFY_DEFERRAL.json"
SAFE = re.compile(r"[A-Za-z0-9_.-]{1,64}")


class ContractError(RuntimeError):
    """A source did not say what the contract needs: the generator refuses, it never guesses (B.10)."""


def _tree(rel: str, root: Path) -> ast.Module:
    try:
        return ast.parse((root / rel).read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise ContractError(f"cannot read {rel}: {exc}") from None


def _assign(tree: ast.Module, name: str, rel: str) -> ast.expr:
    found = [n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    found += [n.value for n in tree.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == name and n.value is not None]
    if len(found) != 1:
        raise ContractError(f"{rel}: expected exactly one module-level assignment of {name}, found {len(found)}")
    return found[0]


def _literal(rel: str, name: str, root: Path):
    try:
        return ast.literal_eval(_assign(_tree(rel, root), name, rel))
    except ValueError:
        raise ContractError(f"{rel}: {name} is not a literal") from None


def _utc_datetime(node: ast.expr, what: str) -> dt.datetime:
    """`datetime(Y, M, D, tzinfo=timezone.utc)` -> that instant."""
    ok = (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "datetime" and len(node.args) == 3
          and len(node.keywords) == 1 and node.keywords[0].arg == "tzinfo" and ast.unparse(node.keywords[0].value) == "timezone.utc")
    if not ok:
        raise ContractError(f"{what} is not datetime(Y, M, D, tzinfo=timezone.utc)")
    return dt.datetime(*(ast.literal_eval(a) for a in node.args), tzinfo=dt.timezone.utc)


def horizon(root: Path) -> dict:
    node = _assign(_tree(WRITER, root), "DEFAULT_HORIZON", WRITER)
    if not (isinstance(node, ast.Tuple) and len(node.elts) == 2):
        raise ContractError("DEFAULT_HORIZON is not a two-element tuple")
    start = _utc_datetime(node.elts[0], "DEFAULT_HORIZON start")
    m = re.search(r"\bborn (\d{4})-(\d{2})-(\d{2})\b", (root / BIRTH_PATH).read_text(encoding="utf-8"))
    if not m:
        raise ContractError(f"{BIRTH_PATH}: no 'born YYYY-MM-DD' (§B Subject)")
    year, month, day = (int(x) for x in m.groups())
    try:
        end = dt.datetime(year + HORIZON_YEARS, month, day, tzinfo=dt.timezone.utc)
    except ValueError:
        raise ContractError("birth date + 100 years is not a calendar date") from None
    if not start < end:
        raise ContractError("horizon start is not before its end")
    return {"start": start.isoformat(), "end": end.isoformat(), "interval": "[start, end)",
            "start_source": f"{WRITER} DEFAULT_HORIZON[0]", "end_source": f"{BIRTH_PATH} §B birth date + {HORIZON_YEARS} years"}


def classes(root: Path, shared_args: dict) -> dict:
    membership = _literal(REGISTRY, "ROW_MEMBERSHIP", root)
    scored = sorted(c for c, k in membership.items() if k is not None)
    if not scored:
        raise ContractError("no scored class")
    return {"selector": shared_args["classes"], "scored": scored, "count": len(scored), "source": f"{REGISTRY} ROW_MEMBERSHIP (value not None)"}


def policy(root: Path, pack: Path | None) -> dict:
    """The sink policy an unmarked run takes is the `else` arm of the writer's own selection; STRICT = the raise policy (contact_certify.POLICY_RAISE)."""
    selected = [n.value for n in ast.walk(_tree(WRITER, root)) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "policy" for t in n.targets)
                and isinstance(n.value, ast.IfExp)]
    if len(selected) != 1 or not isinstance(selected[0].orelse, ast.Attribute):
        raise ContractError(f"{WRITER}: the writer's sink-policy selection (policy = A if slice else B) was not found exactly once")
    name = selected[0].orelse.attr
    sink = _literal(CERTIFY, name, root)
    final_key = re.search(r'ctx\.config\.get\("(gochara_v5_final_rules)"\)', (root / WRITER).read_text(encoding="utf-8"))
    if not final_key:
        raise ContractError(f"{WRITER}: the final-rules config key was not found")
    defer_key = _literal(WRITER, "DEFER_VERIFY_KEY", root)
    out = {"certification": {"sink_policy": sink, "strict": name == "POLICY_RAISE", "source": f"{WRITER} policy selection, unmarked arm ({name})"},
           "config_keys": {"final_rules": final_key.group(1), "defer_in_build_verify": defer_key, "result_policy": _literal(WRITER, "_RESULT_POLICY_KEY", root)},
           "final_rules": None, "defer_in_build_verify": None, "result_policy": None, "source": None}
    if pack is not None:
        body = (pack / PACK_FILE).read_bytes()
        args = (json.loads(body).get("carrier") or {}).get("args") or {}
        for key in ("final_rules", "defer_in_build_verify"):
            if args.get(key) not in ("true", "false"):
                raise ContractError(f"{PACK_FILE} carrier.args.{key} is not 'true' or 'false'")
            out[key] = args[key] == "true"
        if args.get("result_policy") not in _literal(SHARED, "CENTURY_RESULT_POLICIES", root):
            raise ContractError(f"{PACK_FILE} carrier.args.result_policy is not one of the named result policies")
        out["result_policy"] = args["result_policy"]
        out["source"] = {"file": PACK_FILE, "sha256": hashlib.sha256(body).hexdigest(), "ruling": "SR-W3-SHAPE 3; SR-W34-PREP-RULINGS 1"}
    return out


def cap(root: Path) -> dict:
    text = (root / CAP_MIGRATION).read_text(encoding="utf-8")
    values = re.findall(r"^\s*SET writer_timeout_seconds\s*=\s*(\d+)\s*$", text, re.M)
    if len(values) != 1:
        raise ContractError(f"{CAP_MIGRATION}: expected exactly one 'SET writer_timeout_seconds = N'")
    return {"writer_timeout_seconds": int(values[0]), "source": CAP_MIGRATION}


_PIPELINE_JOB = "deploy-pipeline-job"
_PIPELINE_DOCKERFILE = "./platform/python-sidecar/Dockerfile.pipeline"
_PIPELINE_BUILD_STEP = "Build and push pipeline job image"
_PIPELINE_REPOINT_STEP = "Re-point Cloud Run Job at the new image"
_VERIFIED_ACTION = ".github/actions/build-verified-cgm-image"
_PROBE = f"{_VERIFIED_ACTION}/probe_registration.py"
_PROBE_RUN = f"python3 {_PROBE}"
_SOURCE_TAG = ":${{ env.DEPLOY_SHA }}"
_SOURCE_ENV = "DEPLOY_SHA: ${{ github.event.workflow_run.head_sha || github.sha }}"
_VERIFIED_REF = '"${CGM_VERIFIED_PIPELINE_REF:?missing verified Pipeline image}"'
_REGION_NAMES = ("GCP_REGION", "DEPLOY_REGION")
_SAFE_FLAG = re.compile(r"[A-Za-z0-9_.@:/=,-]+")
_REPOSITORY = re.compile(r"[a-z0-9.-]+(?:/[a-z0-9_.-]+)*/brahma-pipeline")

# Reviewed top-level proof groups of the local action's probe. Fingerprint the
# AST, not source bytes, and ignore docstrings and empty newer AST fields.
# A substantive proof change requires requalification of the affected group.
_PROBE_BINDINGS = (
    ("validated source and platform", "SIDECAR PIPELINE REGISTRY SOURCE_ROOT BUILD_SHAPES PACKAGE_ROOTS MODULES DIGEST COMMIT MANIFEST_TYPES INDEX_TYPES ProbeFailure require digest command manifest_identity inspect_loaded loaded_build_id source_commit source_hashes probe_image verify_registration", "63720afa9e653ee995065e979af9292e49d2cf0738b7ee814eb1c15cd4c58f6c"),
    ("verified carrier construction", "check_pipeline_tag pipeline_reference verified_pipeline_reference verify_build", "1cb0f0c82b5bcfe0537b3da2ba0fe4378397bfd4a10857e5df6a8c3c512f46e2"),
    ("repoint readback and dispatch", "post_repoint main", "75e51523cbc4ab41ec273a853ab4e1272c0ee38d30a743d4c8c60bbe68c906b7"),
)


# Reviewed single-build local-export policy. The original push-only policy above
# remains separately supported. Every definition belongs to one proof group.
_LOADED_PROBE_BINDINGS = (
    ('validated source and platform', 'SIDECAR PIPELINE REGISTRY SOURCE_ROOT BUILD_SHAPES PACKAGE_ROOTS MODULES DIGEST COMMIT MANIFEST_TYPES INDEX_TYPES ProbeFailure require digest command json_object content_digest registry_manifest manifest_identity inspect_image check_probe_platform check_loaded_descriptor build_metadata loaded_build_id ordinary_image_id release_image_id source_commit source_hashes probe_image verify_registration', '9f6b0cc99c254fb65f454477b4cb17f0503f04fa7528143004004d100410456e'),
    ('verified carrier construction', 'check_release_tag pipeline_reference verified_pipeline_reference verify_build', 'ee407e932c49566715b2c50cc5414f8fb344f4c3604b2f4697cafaffa2036aad'),
    ('repoint readback and dispatch', 'post_repoint main', '50fbcf675304e8fa886ec2bc91006586cbcc50d4d3adad38537bc08ce891115a'),
)
_LOADED_PROBE_ORDER = 'c54cef725bdb11c9f6e6e4d1cdf673a49a361b35e7be362407880762168ae0e5'
_LOADED_PROBE_SCAFFOLDING = 'aa2007ece33612984bd23e7e8b027bfa9a818924b944f567934d73c319351c2b'

# Exact local identity binding and three retained package checks before repoint.
# Keep these literal commands paired with the loaded action/probe policy.
_LOADED_REPOINT_PREAMBLE = (
    'local_image="${CGM_VERIFIED_LOCAL_IMAGE_ID:?missing verified local image}"',
    '[[ "$local_image" =~ ^sha256:[a-f0-9]{64}$ ]] || exit 1',
    'local_platform="$(docker image inspect --platform=linux/amd64 --format \'{{.Id}}\' "$local_image")" || exit 1',
    'test "$local_platform" = "${CGM_VERIFIED_IMAGE##*@}" || exit 1',
    'docker run --rm --pull=never --platform=linux/amd64 --network=none --entrypoint python "$local_image" \\',
    '-c "import ga_writers; print(\'ga_writers OK:\', ga_writers.__file__)"',
    'docker run --rm --pull=never --platform=linux/amd64 --network=none --entrypoint /bin/sh "$local_image" \\',
    '-n /app/platform/python-sidecar/scripts/kala_gochara_cutover/century_run_4_1.sh',
    'docker run --rm --pull=never --platform=linux/amd64 --network=none --entrypoint python "$local_image" \\',
    '-c "import sys; sys.path.insert(0, \'/app/platform/python-sidecar/scripts/kala_gochara_cutover\'); import common; print(\'cutover common OK:\', common.__file__)"',
)


def _syntax(value):
    if isinstance(value, ast.AST):
        fields = {}
        for key, item in ast.iter_fields(value):
            if key == "type_params" and not item:
                continue
            if key == "body" and isinstance(item, list) and item:
                first = item[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    item = item[1:]
            fields[key] = _syntax(item)
        return [type(value).__name__, fields]
    if isinstance(value, list):
        return [_syntax(item) for item in value]
    if isinstance(value, (bytes, complex)) or value is Ellipsis:
        return [type(value).__name__, repr(value)]
    return value


def _syntax_hash(nodes) -> str:
    data = json.dumps(_syntax(nodes), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode()).hexdigest()


def _verified_repository(root: Path, *, loaded: bool = False) -> str:
    action = (root / _VERIFIED_ACTION / "action.yml").read_text(encoding="utf-8")
    lines = [line.rstrip() for line in action.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    top = [line.split(":", 1)[0] for line in lines if not line[0].isspace()]
    if len(top) != 4 or set(top) != {"name", "description", "inputs", "runs"}:
        raise ContractError("the verified Pipeline action has unexpected or duplicate top-level fields")
    numbered = list(enumerate(lines, 1))
    inputs = _section(numbered, "inputs:", 0)
    keys = [line for _, line in inputs if line.startswith("  ") and not line.startswith("   ")]
    expected_inputs = {
        "context": ["    required: true"], "file": ["    required: true"],
        "push": ["    default: 'false'"], "load": ["    default: 'false'"],
        "tags": ["    required: true"], "cache-from": [], "cache-to": [],
    }
    if keys != [f"  {key}:" for key in expected_inputs] or lines.count("runs:") != 1:
        raise ContractError("the verified Pipeline action must declare its exact inputs and composite")
    for name, flags in expected_inputs.items():
        got = [line for _, line in _section(inputs, f"  {name}:", 2) if not line.startswith("    description:")]
        if got != flags:
            raise ContractError("the verified Pipeline action must keep its reviewed push-only input defaults")
    expected = """runs:
  using: composite
  steps:
    - id: build
      uses: docker/build-push-action@v6
      with:
        context: ${{ inputs.context }}
        file: ${{ inputs.file }}
        push: ${{ inputs.push }}
        load: ${{ inputs.load }}
        tags: ${{ inputs.tags }}
        cache-from: ${{ inputs.cache-from }}
        cache-to: ${{ inputs.cache-to }}
    - name: Verify exact packaged CGM registration
      shell: bash
      env:
        CGM_BUILD_CONTEXT: ${{ inputs.context }}
        CGM_BUILD_FILE: ${{ inputs.file }}
        CGM_BUILD_PUSH: ${{ inputs.push }}
        CGM_BUILD_LOAD: ${{ inputs.load }}
        CGM_BUILD_TAGS: ${{ inputs.tags }}
        CGM_BUILD_IMAGE_ID: ${{ steps.build.outputs.imageid }}
        CGM_BUILD_DIGEST: ${{ steps.build.outputs.digest }}
        CGM_BUILD_METADATA: ${{ steps.build.outputs.metadata }}
      run: python3 "$GITHUB_ACTION_PATH/probe_registration.py" verify-build"""
    if loaded:
        expected = expected.replace(
            "        load: ${{ inputs.load }}\n",
            "        load: ${{ inputs.load }}\n"
            "        outputs: ${{ inputs.push == 'true' && 'type=docker' || '' }}\n"
            "        attests: ${{ inputs.push == 'true' && 'type=provenance,mode=max' || '' }}\n",
        ).replace(
            "        CGM_BUILD_LOAD: ${{ inputs.load }}",
            "        CGM_BUILD_LOAD: ${{ inputs.push == 'true' && 'true' || inputs.load }}",
        )
    if lines[lines.index("runs:"):] != expected.splitlines():
        raise ContractError("the verified Pipeline action must bind the exact Buildx output to the image probe")

    probe = _tree(_PROBE, root)
    definitions = {}
    scaffolding = []
    order = []
    for node in probe.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            name = node.name
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        else:
            scaffolding.append(node)
            order.append(type(node).__name__)
            continue
        if name in definitions:
            raise ContractError("duplicate definition in the verified Pipeline probe")
        definitions[name] = node
        order.append(name)
    expected_order = _LOADED_PROBE_ORDER if loaded else "1ed4293893c0a54883fb0a8701a7749ecf83aa2cf82a2339cf44ed2232c674c0"
    if _syntax_hash(order) != expected_order:
        raise ContractError("the verified Pipeline probe changed its reviewed declaration order")
    expected_scaffolding = _LOADED_PROBE_SCAFFOLDING if loaded else "aa2007ece33612984bd23e7e8b027bfa9a818924b944f567934d73c319351c2b"
    if _syntax_hash(scaffolding) != expected_scaffolding:
        raise ContractError("the verified Pipeline probe must have its reviewed imports and entry point")
    known = set()
    bindings = _LOADED_PROBE_BINDINGS if loaded else _PROBE_BINDINGS
    for group, members, expected_hash in bindings:
        names = members.split()
        known.update(names)
        if any(name not in definitions for name in names) or _syntax_hash([definitions[name] for name in names]) != expected_hash:
            raise ContractError(f"the verified Pipeline probe changed its {group} proof")
    if definitions.keys() != known:
        raise ContractError("unexpected definition in the verified Pipeline probe")
    registry = _literal(_PROBE, "REGISTRY", root)
    component = _literal(_PROBE, "PIPELINE", root)
    return f"{registry}/{component}"


def _section(lines, header: str, indent: int):
    """Return a single exact block with original physical line numbers."""
    starts = [i for i, (_, line) in enumerate(lines) if line == header]
    if len(starts) != 1:
        raise ContractError(f"{DEPLOY}: expected exactly one {header.strip()} block")
    start = starts[0] + 1
    end = next((i for i in range(start, len(lines)) if len(lines[i][1]) - len(lines[i][1].lstrip()) <= indent), len(lines))
    return lines[start:end]


def _named_step(steps, name: str):
    labels = {f'{prefix}{quoted}' for prefix in ("      - name: ", "        name: ")
              for quoted in (name, f'"{name}"', f"'{name}'")}
    indexes = [i for i, step in enumerate(steps) if any(line in labels for _, line in step)]
    if len(indexes) != 1 or steps[indexes[0]][0][1] != f"      - name: {name}":
        raise ContractError(f"{DEPLOY}: expected exactly one {name} step in the Pipeline job")
    return indexes[0], steps[indexes[0]][1:]


def _source_command_lines(lines: list[str]):
    """Expose literal step run scalars for the narrow gcloud argv check."""
    index = 0
    while index < len(lines):
        number, line = index + 1, lines[index]
        index += 1
        match = re.fullmatch(r"(?: {6}- | {8})run:[ \t]*(.*)", line)
        if not match:
            yield number, line
            continue
        value = match[1]
        if re.fullmatch(r">[+-]?(?:[ \t]+#.*)?", value):
            start = index
            while index < len(lines) and (not lines[index].strip() or lines[index].startswith("         ")):
                index += 1
            folded = []
            previous_plain = False
            for part in textwrap.dedent("\n".join(lines[start:index])).splitlines():
                plain = bool(part and not part[0].isspace())
                if previous_plain and plain:
                    folded[-1] += " " + part
                else:
                    folded.append(part)
                previous_plain = plain
            yield from ((number, part) for part in folded)
            continue
        if value.startswith(('"', "'")):
            try:
                script = ast.literal_eval(value)
            except (SyntaxError, ValueError):
                pass  # Keep the raw spelling available to the literal guard.
            else:
                if isinstance(script, str):
                    yield from ((number, part) for part in script.splitlines())
                    continue
        yield number, line


def _target_job_updates(lines: list[str], job_name: str):
    """Find literal gcloud job updates across shell spacing and escaped newlines."""
    physical = []
    separators = ";&|()"
    update = ["run", "jobs", "update"]
    for number, line in _source_command_lines(lines):
        if not physical:
            start = number
        physical.append(line)
        if (len(line) - len(line.rstrip("\\"))) % 2:
            continue
        invocation = textwrap.dedent("\n".join(physical)).replace("\\\n", "")
        physical.clear()
        if "gcloud" not in invocation and job_name not in invocation:
            continue
        lexer = shlex.shlex(invocation, posix=True, punctuation_chars=separators)
        lexer.whitespace_split = True
        try:
            tokens = list(lexer)
        except ValueError:
            if job_name in invocation and "update" in invocation:
                raise ContractError(f"{DEPLOY}: cannot read a possible Pipeline update argv") from None
            continue
        command = []
        matched = False
        for token in [*tokens, ";"]:
            if token and all(char in separators for char in token):
                for i in range(1, len(command) - len(update)):
                    if (command[i:i + 3] == update and job_name in command[i + 3:]
                            and any(Path(arg).name == "gcloud" for arg in command[:i])):
                        flags = {arg.split("=", 1)[0] for arg in command if arg.startswith("--")}
                        matched = True
                        yield start, flags
                command = []
            else:
                command.append(token)
        # Retain the prior exact textual protection for a visible update whose
        # outer scalar or quoting does not produce a literal argv match.
        if not matched and f"gcloud run jobs update {job_name} " in invocation:
            flags = set(re.findall(r"\s(--(?:image|task-timeout|flags-file))(?:=|\s|$)", invocation))
            if flags:
                yield start, flags


def _visible_unbound_repoint(jobs, repoint, job_name: str) -> bool:
    """Decline visible mutation clues outside the bound step, even in opaque run syntax."""
    boundaries = [0, *(
        i for i, (_, line) in enumerate(jobs)
        if re.fullmatch(r"  [A-Za-z0-9_.-]+:", line) or line.startswith("      - ")
    ), len(jobs)]
    approved = {number for number, _ in repoint}
    target = re.compile(rf"(?<![\w.-]){re.escape(job_name)}(?![\w.-])")
    action = re.compile(r"""\brun[\s\\'"]+jobs[\s\\'"]+update\b""")
    mutation = re.compile(r"""(?:^|[\s'"])--(?:image|task-timeout|flags-file)(?=[=\s'"]|$)""")
    for start, end in zip(boundaries, boundaries[1:]):
        fragment = jobs[start:end]
        if any(number in approved for number, _ in fragment):
            continue
        text = "\n".join(line for _, line in fragment)
        if re.search(r"(?<![\w.-])gcloud(?![\w.-])", text) and action.search(text) and target.search(text) and mutation.search(text):
            return True
    return False


def _check_repoint_tail(steps, image_ref: str, *, loaded: bool = False) -> None:
    """The reviewed Pipeline tail has only the two image smoke steps."""
    expected = r"""      - name: Verify ga_writers is importable in the pushed image
        run: |
          docker run --rm --entrypoint python \
            IMAGE_REFERENCE \
            -c "import ga_writers; print('ga_writers OK:', ga_writers.__file__)"
      - name: Verify the gochara century runner exists in the pushed image
        run: |
          docker run --rm --entrypoint /bin/sh \
            IMAGE_REFERENCE \
            -n /app/platform/python-sidecar/scripts/kala_gochara_cutover/century_run_4_1.sh
          docker run --rm --entrypoint python \
            IMAGE_REFERENCE \
            -c "import sys; sys.path.insert(0, '/app/platform/python-sidecar/scripts/kala_gochara_cutover'); import common; print('cutover common OK:', common.__file__)"
"""
    if loaded:
        expected = ""
    if [line for step in steps for _, line in step] != expected.replace("IMAGE_REFERENCE", image_ref).splitlines():
        raise ContractError(f"{DEPLOY}: unexpected Pipeline step after the verified repoint")


def _pipeline_repoint(root: Path, *, job_name: str, region: str) -> tuple[str, dict]:
    workflow = (root / DEPLOY).read_text(encoding="utf-8").splitlines()
    lines = [(i, line.rstrip()) for i, line in enumerate(workflow, 1)
             if line.strip() and not line.lstrip().startswith("#")]
    top = [line for _, line in lines if not line[0].isspace()]
    if top.count("jobs:") != 1 or top.count("env:") != 1 or any(
        not re.fullmatch(r"(?:name: .+|on:|concurrency:|env:|jobs:)", line) for line in top
    ):
        raise ContractError(f"{DEPLOY}: unexpected top-level workflow structure or shell defaults")
    environment = _section(lines, "env:", 0)
    env = [line.strip() for _, line in environment]
    source_rows = [line for line in env if line.split(":", 1)[0].strip("\"'") == "DEPLOY_SHA"]
    if source_rows != [_SOURCE_ENV]:
        raise ContractError(f"{DEPLOY}: unexpected Pipeline DEPLOY_SHA source")
    region_rows = [
        line for _, line in environment
        if line.strip().split(":", 1)[0].strip("\"'") in _REGION_NAMES
    ]
    if len(region_rows) != 1:
        raise ContractError(f"{DEPLOY}: expected one literal Pipeline region source")
    region_name = region_rows[0].strip().split(":", 1)[0]
    if region_rows[0] != f"  {region_name}: {region}":
        raise ContractError(f"{DEPLOY}: unexpected Pipeline region source")
    region_reference = "${{ env." + region_name + " }}"
    if any(line.startswith(("CGM_VERIFIED_", "<<:")) or line[0] in "\"'" for line in env):
        raise ContractError(f"{DEPLOY}: unexpected Pipeline environment carrier")
    jobs = _section(lines, "jobs:", 0)
    if any(not re.fullmatch(r"  [a-zA-Z0-9_.-]+:", line)
           for _, line in jobs if len(line) - len(line.lstrip()) == 2):
        raise ContractError(f"{DEPLOY}: unsupported job alias or inline job definition")
    job = _section(jobs, f"  {_PIPELINE_JOB}:", 2)
    job_fields = [line.split(":", 1)[0].strip() for _, line in job if len(line) - len(line.lstrip()) == 4]
    if len(job_fields) != len(set(job_fields)) or not set(job_fields) <= {
        "name", "needs", "if", "runs-on", "permissions", "steps",
    }:
        raise ContractError(f"{DEPLOY}: unsupported Pipeline job override")
    body = _section(job, "    steps:", 4)
    starts = [i for i, (_, line) in enumerate(body) if line.startswith("      - ")]
    if not starts or starts[0] != 0:
        raise ContractError(f"{DEPLOY}: malformed Pipeline steps")
    steps = [body[i:j] for i, j in zip(starts, starts[1:] + [len(body)])]
    checkout_idx, checkout = _named_step(steps, "Checkout")
    build_idx, build = _named_step(steps, _PIPELINE_BUILD_STEP)
    repoint_idx, repoint = _named_step(steps, _PIPELINE_REPOINT_STEP)
    if [line for _, line in checkout] != [
        "        uses: actions/checkout@v4", "        with:", "          ref: ${{ env.DEPLOY_SHA }}",
    ] or not checkout_idx < build_idx == repoint_idx - 1:
        raise ContractError(f"{DEPLOY}: the exact Pipeline checkout, build and repoint must be ordered")
    possible_builders = ("uses: docker/build-push-action@", f"uses: ./{_VERIFIED_ACTION}", f"file: {_PIPELINE_DOCKERFILE}")
    if any(line.strip().removeprefix("- ").startswith(possible_builders)
           for i, step in enumerate(steps) if i != build_idx for _, line in step):
        raise ContractError(f"{DEPLOY}: unexpected alternate Pipeline builder")
    if any(line.strip().removeprefix("- ").startswith("uses: actions/checkout@")
           for i, step in enumerate(steps) if i != checkout_idx for _, line in step):
        raise ContractError(f"{DEPLOY}: unexpected alternate Pipeline checkout")
    command = f"gcloud run jobs update {job_name} "
    updates = list(_target_job_updates(workflow, job_name))
    job_lines = {number for number, _ in job}
    if sum(number in job_lines for number, _ in updates) != 1:
        raise ContractError(f"{DEPLOY}: expected one actual Pipeline job update in the deployment job")
    if any(number not in job_lines and flags & {"--image", "--task-timeout", "--flags-file"}
           for number, flags in updates):
        raise ContractError(f"{DEPLOY}: unexpected image or timeout repoint outside the Pipeline job")
    if _visible_unbound_repoint(jobs, repoint, job_name):
        raise ContractError(f"{DEPLOY}: ambiguous Pipeline image or timeout mutation outside the reviewed repoint")
    if not repoint or repoint[0][1] != "        run: |" or any(not line.startswith("          ") for _, line in repoint[1:]):
        raise ContractError(f"{DEPLOY}: the Pipeline repoint must be one unguarded run step")

    body = [(i, line.strip()) for i, line in repoint[1:]]
    loaded = bool(body and body[0][1] == _LOADED_REPOINT_PREAMBLE[0])
    if loaded:
        if [line for _, line in body[:len(_LOADED_REPOINT_PREAMBLE)]] != list(_LOADED_REPOINT_PREAMBLE):
            raise ContractError(f"{DEPLOY}: unexpected Pipeline local image checks")
        body = body[len(_LOADED_REPOINT_PREAMBLE):]
    verified = bool(body and body[0][1] == f"{_PROBE_RUN} verify-repoint")
    if loaded and not verified:
        raise ContractError(f"{DEPLOY}: local image checks require the verified Pipeline repoint")
    if verified:
        if body[-1][1] != f'GOOGLE_CLOUD_REGION="{region_reference}" {_PROBE_RUN} post-repoint':
            raise ContractError(f"{DEPLOY}: the verified Pipeline repoint must immediately check readback")
        body = body[1:-1]
    if len(body) < 4 or body[0][1] != command + "\\" or body[-1][1] != "--quiet":
        raise ContractError(f"{DEPLOY}: expected the contiguous literal Pipeline repoint argv")
    args = {}
    for i, line in body[1:-1]:
        if not line.endswith(" \\") or not line.startswith("--") or "=" not in line:
            raise ContractError(f"{DEPLOY}: split, hidden or unbound Pipeline repoint argument")
        flag, value = line[2:-2].split("=", 1)
        if flag in args:
            raise ContractError(f"{DEPLOY}: duplicate Pipeline repoint argument")
        if flag not in {"region", "image", "task-timeout"} and (
            flag not in {"service-account", "update-secrets", "memory", "cpu", "update-env-vars"} or not _SAFE_FLAG.fullmatch(value)
        ):
            raise ContractError(f"{DEPLOY}: unsupported Pipeline repoint argument")
        args[flag] = (i, value)
    if args.get("region", (None, None))[1] != region_reference or not {"image", "task-timeout"} <= args.keys():
        raise ContractError(f"{DEPLOY}: the actual Pipeline repoint must bind region, image and timeout")
    timeout_line, timeout = args["task-timeout"]
    if not re.fullmatch(r"[1-9][0-9]*", timeout):
        raise ContractError(f"{DEPLOY}: invalid Pipeline task timeout")
    image_ref = args["image"][1]
    if verified:
        if image_ref != _VERIFIED_REF:
            raise ContractError(f"{DEPLOY}: Pipeline image is not the exact verified combined reference")
        repository = _verified_repository(root, loaded=loaded)
    else:
        repository = image_ref.removesuffix(_SOURCE_TAG)
        if repository == image_ref or not _REPOSITORY.fullmatch(repository):
            raise ContractError(f"{DEPLOY}: Pipeline image is not the exact direct source tag")
    uses = f"./{_VERIFIED_ACTION}" if verified else "docker/build-push-action@v6"
    expected_build = [
        f"        uses: {uses}", "        with:", "          context: .",
        f"          file: {_PIPELINE_DOCKERFILE}", "          push: true", "          tags: |",
        f"            {repository}{_SOURCE_TAG}", f"            {repository}:latest",
        "          cache-from: type=gha,scope=brahma-pipeline", "          cache-to: type=gha,mode=max,scope=brahma-pipeline",
    ]
    if [line for _, line in build] != expected_build:
        raise ContractError(f"{DEPLOY}: the exact same-job Pipeline builder must bind the repoint repository and source")
    _check_repoint_tail(steps[repoint_idx + 1:], '"$CGM_VERIFIED_IMAGE"' if verified else image_ref, loaded=loaded)
    return repository, {"cloud_run_task_timeout_seconds": int(timeout), "source": f"{DEPLOY}:{timeout_line}"}


def _deployment_image(root: Path) -> tuple[dict, dict]:
    bindings = {k.lower(): _literal(DISPATCH, k, root) for k in ("LAUNCH_JOB", "LAUNCH_PROJECT", "LAUNCH_REGION")}
    out = {"job": bindings["launch_job"], "project": bindings["launch_project"], "region": bindings["launch_region"]}
    out["repository"], timeout = _pipeline_repoint(root, job_name=out["job"], region=out["region"])
    return out, timeout


def task_timeout(root: Path) -> dict:
    return _deployment_image(root)[1]


def image(root: Path, with_digest: bool) -> dict:
    out, _ = _deployment_image(root)
    out["writer_source_digest"] = writer_source_digest(root) if with_digest else None
    out["digest_source"] = "pipeline.orchestrator.writer_runtime_support.get_writer_source_hash('ka_gochara_v5')"
    return out


def writer_source_digest(root: Path) -> str:
    sidecar = str(root / "platform/python-sidecar")
    sys.path.insert(0, sidecar)
    try:
        from pipeline.orchestrator.writer_runtime_support import get_writer_source_hash
        return get_writer_source_hash("ka_gochara_v5")
    except Exception as exc:     # a missing dependency is a refusal, never a skipped check
        raise ContractError(f"the writer-source digest needs the sidecar dependencies ({type(exc).__name__}); use --no-image for a partial check") from None
    finally:
        sys.path.remove(sidecar)


def _create_columns(text: str, table: str) -> set[str]:
    cols: set[str] = set()
    for m in re.finditer(r"CREATE TABLE (?:IF NOT EXISTS )?(?:public\.)?" + re.escape(table) + r"\s*\(", text):
        depth, j = 1, m.end()
        while depth and j < len(text):
            depth += (text[j] == "(") - (text[j] == ")")
            j += 1
        body = re.sub(r"--[^\n]*", "", text[m.end():j - 1])
        parts, depth, cur = [], 0, ""
        for c in body:
            depth += (c == "(") - (c == ")")
            if c == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += c
        parts.append(cur)
        for part in parts:
            words = part.split()
            if words and words[0].upper() not in ("CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "EXCLUDE", "LIKE") and re.fullmatch(r"[a-z_][a-z0-9_]*", words[0]):
                cols.add(words[0])
    for m in re.finditer(r"ALTER TABLE (?:ONLY )?(?:IF EXISTS )?(?:public\.)?" + re.escape(table) + r"\b(.*?);", text, re.S):
        cols.update(a.group(1) for a in re.finditer(r"ADD COLUMN (?:IF NOT EXISTS )?([a-z_][a-z0-9_]*)", re.sub(r"--[^\n]*", "", m.group(1))))
    return cols


def output_tables(root: Path, shared) -> list[dict]:
    """Every generation-scoped table the century run fills for (chart_id, generation): the shared module's ABSENCE_TABLES (output + near-miss), each proven by its CREATE TABLE
    migration to carry chart_id and generation. class_column: `event_class` when the table has it; the coverage table partitions its class rows by partition_kind = 'event_class'
    in partition_key (its WHERE is recorded)."""
    text = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in sorted((root / "platform/migrations").glob("*.sql")))
    out = []
    for table, extra in shared.ABSENCE_TABLES:
        cols = _create_columns(text, table)
        if not {"chart_id", "generation"} <= cols:
            raise ContractError(f"{table}: no migration creates it with chart_id and generation columns")
        where = re.sub(r"^\s*AND\s+", "", extra).strip() or None
        column = "event_class" if "event_class" in cols else None
        if where and where.replace(" ", "") == "partition_kind='event_class'":
            column = "partition_key" if "partition_key" in cols else None
        out.append({"object": table, "table": "public." + table, "class_column": column, "where": where})
    return out


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def launch_args(shared, pol: dict, hz: dict) -> dict:
    """The request's exact five `args` (F-CHANNEL, SR-W34-PREP-RULINGS 1, OD-1; shared.CENTURY_ARG_KEYS): `classes` all, the two policy booleans as 'true'/'false', the horizon as
    '<start>,<end>' (the committed horizon, verbatim: SR-HORIZON-PUBLIC) and the numeric-result policy. The three policy values are pack-sourced and stay null without --pack. (I) INTERPRETATION: the launch
    args are derived from the facts the contract already commits, so a request that differs from them in any value is refused by `century_contract_problem`."""
    if set(shared.CENTURY_ARG_KEYS) != {"classes", "final_rules", "defer_in_build_verify", "horizon", "result_policy"}:
        raise ContractError("the century request's argument keys changed; the contract's launch_args generator must be reviewed")
    flag = lambda value: None if value is None else ("true" if value else "false")
    return {"classes": "all", "final_rules": flag(pol["final_rules"]), "defer_in_build_verify": flag(pol["defer_in_build_verify"]), "horizon": f"{hz['start']},{hz['end']}",
            "result_policy": pol["result_policy"]}


def derive(root: Path = REPO, pack: Path | None = None, with_digest: bool = True) -> dict:
    root = Path(root)
    shared = _load(root / SHARED, "century_contract_shared")
    pol, hz = policy(root, pack), horizon(root)
    args = launch_args(shared, pol, hz)
    contract = {
        "schema": SCHEMA, "item": shared.CENTURY_ITEM, "rulings": RULINGS,
        "generation": shared.GENERATION, "triggered_by": shared.CENTURY_TRIGGERED_BY,
        "stored_scope": _literal(INPUT_VECTOR, "STORED_SCOPE", root),
        "launch_args": args, "cancel_schema": _literal(CANCEL, "SCHEMA", root),
        "horizon": hz, "classes": classes(root, args), "policy": pol,
        "cap": cap(root), "timeout": task_timeout(root), "image": image(root, with_digest),
        "output_tables": output_tables(root, shared),
    }
    for key in ("generation", "triggered_by", "stored_scope"):
        if not SAFE.fullmatch(contract[key]):
            raise ContractError(f"{key} is not a safe literal")
    if contract["item"] != ITEM:
        raise ContractError("the century item changed")
    check_cap_below_timeout(contract["cap"], contract["timeout"])
    return contract


def check_cap_below_timeout(cap_: dict, timeout_: dict) -> None:
    if cap_["writer_timeout_seconds"] >= timeout_["cloud_run_task_timeout_seconds"]:
        raise ContractError("the writer cap is not below the Cloud Run task timeout: the watchdog could never fire first")


def render(contract: dict) -> bytes:
    return (json.dumps(contract, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def compare(committed: dict, derived: dict, *, with_digest: bool, with_pack: bool) -> list[str]:
    """Why `committed` is not what the sources give. Without --pack the pack-sourced policy values are only type-checked; with --no-image the digest is not compared."""
    want = json.loads(json.dumps(derived))
    have = json.loads(json.dumps(committed))
    if not with_digest:
        want["image"]["writer_source_digest"] = have.get("image", {}).get("writer_source_digest")
    if not with_pack:
        for key in ("final_rules", "defer_in_build_verify", "result_policy", "source"):
            want["policy"][key] = have.get("policy", {}).get(key)
        if have.get("launch_args", {}).get("result_policy") not in _literal(SHARED, "CENTURY_RESULT_POLICIES", REPO):
            return ["launch_args.result_policy is not a named result policy"]
        want["launch_args"]["result_policy"] = have["launch_args"]["result_policy"]
        for key in ("final_rules", "defer_in_build_verify"):
            if not isinstance(have.get("policy", {}).get(key), bool):
                return [f"policy.{key} is not a boolean"]
            if have.get("launch_args", {}).get(key) not in ("true", "false"):
                return [f"launch_args.{key} is not 'true' or 'false'"]
            want["launch_args"][key] = have["launch_args"][key]
    return [k for k in sorted(set(want) | set(have)) if want.get(k) != have.get(k)]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    ap.add_argument("--pack", type=Path, default=None)
    ap.add_argument("--no-image", action="store_true")
    ap.add_argument("--root", type=Path, default=REPO)
    a = ap.parse_args(argv)
    path = a.root / REL
    try:
        if a.write:
            if a.pack is None or a.no_image:
                raise ContractError("--write needs --pack and the image digest: a contract with a null fact is not written")
            body = render(derive(a.root, a.pack, True))
            path.write_bytes(body)
            print(json.dumps({"written": REL, "sha256": sha256(body)}, sort_keys=True))
            return 0
        derived = derive(a.root, a.pack, not a.no_image)
        differing = compare(json.loads(path.read_text(encoding="utf-8")), derived, with_digest=not a.no_image, with_pack=a.pack is not None)
        print(json.dumps({"check": REL, "sha256": sha256(path.read_bytes()), "equal": not differing, "differs_in": differing,
                          "partial": bool(a.no_image or a.pack is None)}, sort_keys=True))
        return 0 if not differing else 1
    except (ContractError, OSError, ValueError) as exc:
        print(f"century_contract: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
