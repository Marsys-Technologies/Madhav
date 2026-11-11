"""Read-only CGM registration probe for the two normal image shapes."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys


SIDECAR = "amjis-sidecar"
PIPELINE = "brahma-pipeline"
REGISTRY = "asia-south1-docker.pkg.dev/madhav-astrology/amjis"
SOURCE_ROOT = "platform/python-sidecar"
BUILD_SHAPES = {
    "./platform/python-sidecar/Dockerfile": (SIDECAR, "./platform"),
    "./platform/python-sidecar/Dockerfile.pipeline": (PIPELINE, "."),
}
PACKAGE_ROOTS = {
    SIDECAR: "/app/python-sidecar",
    PIPELINE: "/app/platform/python-sidecar",
}
MODULES = (
    "bodha_writers.cgm_identity",
    "pipeline.orchestrator.writers.bo_bimba",
    "pipeline.orchestrator.writers.bo_karanajala",
)
DIGEST = re.compile(r"sha256:[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40}")
MANIFEST_TYPES = {
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
}
INDEX_TYPES = {
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
}


class ProbeFailure(ValueError):
    """A fixed, safe diagnostic that can be written to the workflow log."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ProbeFailure(reason)


def digest(value: object) -> str:
    if not isinstance(value, str) or not DIGEST.fullmatch(value):
        raise ProbeFailure("missing or invalid image digest")
    return value


def command(*args: str, data: bytes | None = None, timeout: int = 30) -> bytes:
    result = subprocess.run(
        args,
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=timeout,
    )
    require(result.returncode == 0, f"{args[0]} {args[1]} failed")
    return result.stdout


def manifest_identity(ref: str) -> tuple[str, str]:
    manifest = json.loads(command(
        "docker", "buildx", "imagetools", "inspect", "--format", "{{json .Manifest}}", ref,
    ))
    top = digest(manifest["digest"])
    if manifest["mediaType"] in MANIFEST_TYPES:
        return top, top
    require(manifest["mediaType"] in INDEX_TYPES, "unsupported image manifest")
    matches = [
        item for item in manifest["manifests"]
        if item.get("platform", {}).get("os") == "linux"
        and item.get("platform", {}).get("architecture") == "amd64"
    ]
    require(len(matches) == 1, "expected exactly one Linux AMD64 platform image")
    require(matches[0]["mediaType"] in MANIFEST_TYPES, "unsupported platform manifest")
    return top, digest(matches[0]["digest"])


def inspect_loaded(ref: str, expected_id: str) -> str:
    image = json.loads(command("docker", "image", "inspect", "--format", "{{json .}}", ref))
    image_id = digest(image["Id"])
    require(image_id == expected_id, "loaded image identity mismatch")
    require((image["Os"], image["Architecture"]) == ("linux", "amd64"), "wrong image platform")
    require(not image["Config"].get("Volumes"), "probe image declares writable volumes")
    return image_id


def loaded_build_id() -> str:
    output = os.environ.get("CGM_BUILD_IMAGE_ID")
    metadata = json.loads(os.environ.get("CGM_BUILD_METADATA") or "{}")
    config = metadata.get("containerimage.config.digest")
    if output and config:
        require(output == config, "contradictory Buildx image IDs")
    return digest(output or config)


def source_commit() -> str:
    commit = os.environ["DEPLOY_SHA"]
    require(COMMIT.fullmatch(commit) is not None, "invalid deployment source")
    return commit


def check_pipeline_tag(tag: str, expected: tuple[str, str]) -> None:
    require(manifest_identity(tag) == expected, "Pipeline commit tag does not match the probed image")


def pipeline_reference(commit: str, image: str) -> str:
    repository = f"{REGISTRY}/{PIPELINE}"
    prefix = f"{repository}@"
    require(COMMIT.fullmatch(commit) is not None, "invalid Pipeline source")
    require(image.startswith(prefix), "wrong verified Pipeline repository")
    return f"{repository}:{commit}@{digest(image.removeprefix(prefix))}"


def verified_pipeline_reference() -> str:
    image = os.environ.get("CGM_VERIFIED_IMAGE", "")
    reference = pipeline_reference(source_commit(), image)
    require(
        os.environ.get("CGM_VERIFIED_PIPELINE_REF") == reference,
        "missing or rebound verified Pipeline reference",
    )
    return reference


def source_hashes(commit: str) -> list[str]:
    return [
        hashlib.sha256(command("git", "show", f"{commit}:{SOURCE_ROOT}/{name.replace('.', '/')}.py")).hexdigest()
        for name in MODULES
    ]


def probe_image(component: str, image_id: str, expected: list[str]) -> None:
    output = command(
        "docker", "run", "--pull=never", "--rm", "-i", "--network=none", "--read-only",
        "--cap-drop=ALL", "--security-opt=no-new-privileges", "--entrypoint=/usr/bin/env",
        image_id, "-i", "PATH=/usr/local/bin:/usr/bin:/bin", "python", "-BI",
        "-X", "pycache_prefix=/dev/null", "-",
        "inside", component, *expected,
        data=Path(__file__).read_bytes(), timeout=30,
    )
    require(output == b"CGM registration verified\n", "missing exact packaged probe result")


def verify_build() -> None:
    component, context = BUILD_SHAPES[os.environ["CGM_BUILD_FILE"]]
    require(os.environ["CGM_BUILD_CONTEXT"] == context, "wrong Docker build context")
    mode = (os.environ["CGM_BUILD_PUSH"], os.environ["CGM_BUILD_LOAD"])
    tags = os.environ["CGM_BUILD_TAGS"].splitlines()
    head = command("git", "rev-parse", "HEAD").decode().strip()
    require(COMMIT.fullmatch(head) is not None, "invalid checkout source")
    expected = source_hashes(head)

    if mode == ("false", "true"):
        local_tag = f"{component}:pr-check"
        require(tags == [local_tag], "unexpected ordinary image tag")
        image_id = inspect_loaded(local_tag, loaded_build_id())
        probe_image(component, image_id, expected)
        print(f"CGM {component} source={head} image={image_id} registration verified")
        return

    require(mode == ("true", "false"), "unsupported build export mode")
    require(head == source_commit(), "deployment checkout mismatch")
    repository = f"{REGISTRY}/{component}"
    commit_tag = f"{repository}:{head}"
    require(tags == [commit_tag, f"{repository}:latest"], "unexpected release image tags")
    build_digest = digest(os.environ.get("CGM_BUILD_DIGEST"))
    top, platform = manifest_identity(f"{repository}@{build_digest}")
    require(top == build_digest, "registry image differs from Buildx output")
    image = f"{repository}@{platform}"
    manifest = json.loads(command("docker", "buildx", "imagetools", "inspect", "--raw", image))
    require(manifest["mediaType"] in MANIFEST_TYPES, "expected a platform image manifest")
    expected_id = digest(manifest["config"]["digest"])
    command("docker", "pull", "--platform", "linux/amd64", image, timeout=180)
    image_id = inspect_loaded(image, expected_id)
    probe_image(component, image_id, expected)
    if component == PIPELINE:
        check_pipeline_tag(commit_tag, (top, platform))

    # Publish only validated, non-secret identifiers to later steps of this job.
    with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as env_file:
        env_file.write(f"CGM_VERIFIED_IMAGE={image}\n")
        if component == PIPELINE:
            env_file.write(f"CGM_VERIFIED_PIPELINE_REF={pipeline_reference(head, image)}\n")
    print(f"CGM {component} source={head} image={image} registration verified")


def post_repoint() -> None:
    reference = verified_pipeline_reference()
    configured = command(
        "gcloud", "run", "jobs", "describe", "brahma-build-pipeline-job",
        "--region", os.environ["GCP_REGION"],
        "--format=value(spec.template.spec.template.spec.containers[0].image)",
    ).decode().removesuffix("\n")
    require(configured == reference, "configured Pipeline image is not the verified combined reference")
    print(f"CGM Pipeline configuration verified image={reference}")


def verify_registration(root: Path, expected: list[str]) -> None:
    require(len(expected) == len(MODULES), "missing source fingerprints")
    paths = []
    for name, checksum in zip(MODULES, expected):
        path = root / f"{name.replace('.', '/')}.py"
        require(path.resolve(strict=True) == path, "shadowed packaged source")
        require(hashlib.sha256(path.read_bytes()).hexdigest() == checksum, "packaged source hash mismatch")
        paths.append(path)

    sys.path.insert(0, str(root))
    identity, bimba, karanajala = (importlib.import_module(name) for name in MODULES)
    for module, path in zip((identity, bimba, karanajala), paths):
        require(Path(module.__file__).resolve(strict=True) == path, "wrong loaded module origin")
    registry = importlib.import_module("pipeline.orchestrator.writers")
    for asset, cls in (
        ("bo_bimba", bimba.BoBimbaWriter),
        ("bo_karanajala", karanajala.BoKaranajalaWriter),
    ):
        require(issubclass(cls, registry.WriterBase), "wrong writer base")
        require(registry.WRITER_REGISTRY.get(asset) is cls, "incorrect concrete registration")

    for module, aliases in (
        (bimba, {
            "_SUBJECT_TO_GRAHA": "SUBJECT_TO_GRAHA",
            "_YOGA_NODE_CLASSES": "YOGA_NODE_CLASSES",
            "_yoga_config_name": "_yoga_config_name",
            "yoga_node_subject": "yoga_node_subject",
        }),
        (karanajala, {
            "_GRAHA_SUBJECT_MAP": "SUBJECT_TO_GRAHA",
            "_YOGA_NODE_CLASSES": "YOGA_NODE_CLASSES",
            "_yoga_node_subject": "yoga_node_subject",
        }),
    ):
        for old, shared in aliases.items():
            require(getattr(module, old) is getattr(identity, shared), "incorrect historical alias identity")


def main() -> None:
    mode, *args = sys.argv[1:]
    if mode == "verify-build" and not args:
        verify_build()
    elif mode == "verify-repoint" and not args:
        verified_pipeline_reference()
    elif mode == "post-repoint" and not args:
        post_repoint()
    elif mode == "inside":
        component, *expected = args
        verify_registration(Path(PACKAGE_ROOTS[component]), expected)
        print("CGM registration verified")
    else:
        raise ProbeFailure("invalid probe mode")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never print raw registry, subprocess, or application output.
        if isinstance(exc, ProbeFailure):
            print(f"CGM verification failed: {exc}", file=sys.stderr)
        else:
            print("CGM verification failed: missing or invalid evidence", file=sys.stderr)
        raise SystemExit(1) from None
