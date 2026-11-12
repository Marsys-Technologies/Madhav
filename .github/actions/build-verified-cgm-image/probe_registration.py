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


def command(*args: str, stage: str, data: bytes | None = None, timeout: int = 30) -> bytes:
    try:
        result = subprocess.run(
            args,
            input=data,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise ProbeFailure(f"{stage} timed out after {timeout}s") from None
    except OSError:
        raise ProbeFailure(f"{stage} could not start") from None
    require(result.returncode == 0, f"{stage} failed")
    return result.stdout


def json_object(data: bytes | str, stage: str) -> dict:
    try:
        parsed = json.loads(data)
    except (UnicodeError, ValueError):
        raise ProbeFailure(f"{stage} returned invalid JSON") from None
    require(isinstance(parsed, dict), f"{stage} returned an invalid object")
    return parsed


def content_digest(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def registry_manifest(ref: str, stage: str) -> tuple[str, dict]:
    raw = command("docker", "buildx", "imagetools", "inspect", "--raw", ref, stage=stage)
    return content_digest(raw), json_object(raw, stage)


def manifest_identity(ref: str, *, stage: str = "registry image manifest") -> tuple[str, str]:
    top, manifest = registry_manifest(ref, stage)
    if manifest.get("mediaType") in MANIFEST_TYPES:
        return top, top
    require(manifest.get("mediaType") in INDEX_TYPES, "unsupported image manifest")
    matches = [
        item for item in manifest["manifests"]
        if item.get("platform", {}).get("os") == "linux"
        and item.get("platform", {}).get("architecture") == "amd64"
    ]
    require(len(matches) == 1, "expected exactly one Linux AMD64 platform image")
    require(matches[0].get("mediaType") in MANIFEST_TYPES, "unsupported platform manifest")
    return top, digest(matches[0].get("digest"))


def inspect_image(ref: str, *, platform: bool = False) -> dict:
    stage = "local AMD64 image inspection" if platform else "local image inspection"
    platform_args = ("--platform=linux/amd64",) if platform else ()
    output = command(
        "docker", "image", "inspect", *platform_args, "--format", "{{json .}}", ref, stage=stage,
    )
    return json_object(output, stage)


def check_probe_platform(image: dict) -> None:
    require((image.get("Os"), image.get("Architecture")) == ("linux", "amd64"), "wrong image platform")
    config = image.get("Config")
    require(isinstance(config, dict), "missing loaded image configuration")
    require(not config.get("Volumes"), "probe image declares writable volumes")


def check_loaded_descriptor(image: dict, expected_id: str, media_types: set[str]) -> None:
    descriptor = image.get("Descriptor")
    require(isinstance(descriptor, dict), "missing loaded image descriptor")
    require(
        digest(image.get("Id")) == expected_id and digest(descriptor.get("digest")) == expected_id,
        "loaded image identity mismatch",
    )
    require(descriptor.get("mediaType") in media_types, "unsupported loaded image descriptor")


def build_metadata() -> dict:
    return json_object(os.environ.get("CGM_BUILD_METADATA") or "{}", "Buildx metadata")


def loaded_build_id() -> str:
    output = os.environ.get("CGM_BUILD_IMAGE_ID")
    config = build_metadata().get("containerimage.config.digest")
    if output and config:
        require(output == config, "contradictory Buildx image IDs")
    return digest(output or config)


def ordinary_image_id(tag: str) -> str:
    image = inspect_image(tag)
    image_id = digest(image.get("Id"))
    if image.get("Descriptor") is None:
        # The classic image store addresses a loaded image by its config digest.
        require(image_id == loaded_build_id(), "loaded image identity mismatch")
    else:
        # With containerd, Buildx and Docker address the manifest or index.
        check_loaded_descriptor(image, digest(os.environ.get("CGM_BUILD_DIGEST")), MANIFEST_TYPES | INDEX_TYPES)
    check_probe_platform(image)
    return image_id


def release_image_id(tag: str, platform_digest: str) -> str:
    image = inspect_image(tag)
    local_id = digest(image.get("Id"))
    check_loaded_descriptor(image, local_id, MANIFEST_TYPES | INDEX_TYPES)
    selected = inspect_image(local_id, platform=True)
    # A matching immutable manifest also binds the config digest and layer descriptors it contains.
    check_loaded_descriptor(selected, platform_digest, MANIFEST_TYPES)
    check_probe_platform(selected)
    return local_id


def source_commit() -> str:
    commit = os.environ["DEPLOY_SHA"]
    require(COMMIT.fullmatch(commit) is not None, "invalid deployment source")
    return commit


def check_release_tag(tag: str, expected: tuple[str, str]) -> None:
    require(
        manifest_identity(tag, stage="release commit tag inspection") == expected,
        "release commit tag does not match the probed image",
    )


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
        hashlib.sha256(command(
            "git", "show", f"{commit}:{SOURCE_ROOT}/{name.replace('.', '/')}.py", stage="source fingerprint",
        )).hexdigest()
        for name in MODULES
    ]


def probe_image(component: str, image_id: str, expected: list[str]) -> None:
    output = command(
        "docker", "run", "--pull=never", "--rm", "-i", "--network=none", "--read-only",
        "--cap-drop=ALL", "--security-opt=no-new-privileges", "--platform=linux/amd64", "--entrypoint=/usr/bin/env",
        image_id, "-i", "PATH=/usr/local/bin:/usr/bin:/bin", "python", "-BI",
        "-X", "pycache_prefix=/dev/null", "-",
        "inside", component, *expected,
        stage="isolated registration probe", data=Path(__file__).read_bytes(), timeout=30,
    )
    require(output == b"CGM registration verified\n", "missing exact packaged probe result")


def verify_build() -> None:
    component, context = BUILD_SHAPES[os.environ["CGM_BUILD_FILE"]]
    require(os.environ["CGM_BUILD_CONTEXT"] == context, "wrong Docker build context")
    mode = (os.environ["CGM_BUILD_PUSH"], os.environ["CGM_BUILD_LOAD"])
    require(mode in {("false", "true"), ("true", "true")}, "unsupported build export mode")
    tags = os.environ["CGM_BUILD_TAGS"].splitlines()
    head = command("git", "rev-parse", "HEAD", stage="checkout source lookup").decode().strip()
    require(COMMIT.fullmatch(head) is not None, "invalid checkout source")
    expected = source_hashes(head)

    if mode == ("false", "true"):
        local_tag = f"{component}:pr-check"
        require(tags == [local_tag], "unexpected ordinary image tag")
        image_id = ordinary_image_id(local_tag)
        probe_image(component, image_id, expected)
        print(f"CGM {component} source={head} image={image_id} registration verified")
        return

    require(head == source_commit(), "deployment checkout mismatch")
    repository = f"{REGISTRY}/{component}"
    commit_tag = f"{repository}:{head}"
    require(tags == [commit_tag, f"{repository}:latest"], "unexpected release image tags")
    build_digest = digest(os.environ.get("CGM_BUILD_DIGEST"))
    top, platform = manifest_identity(f"{repository}@{build_digest}")
    require(top == build_digest, "registry image differs from Buildx output")
    image = f"{repository}@{platform}"
    manifest_digest, manifest = registry_manifest(image, "registry AMD64 manifest")
    require(manifest_digest == platform, "registry AMD64 manifest digest mismatch")
    require(manifest.get("mediaType") in MANIFEST_TYPES, "expected a platform image manifest")
    expected_config = digest(manifest["config"].get("digest"))
    build_config = build_metadata().get("containerimage.config.digest")
    if build_config is not None:
        require(digest(build_config) == expected_config, "Buildx image configuration mismatch")
    image_id = release_image_id(commit_tag, platform)
    probe_image(component, image_id, expected)
    check_release_tag(commit_tag, (top, platform))

    # Publish only validated, non-secret identifiers to later steps of this job.
    with Path(os.environ["GITHUB_ENV"]).open("a", encoding="utf-8") as env_file:
        env_file.write(f"CGM_VERIFIED_IMAGE={image}\nCGM_VERIFIED_LOCAL_IMAGE_ID={image_id}\n")
        if component == PIPELINE:
            env_file.write(f"CGM_VERIFIED_PIPELINE_REF={pipeline_reference(head, image)}\n")
    print(f"CGM {component} source={head} image={image} config={expected_config} local={image_id} registration verified")


def post_repoint() -> None:
    reference = verified_pipeline_reference()
    configured = command(
        "gcloud", "run", "jobs", "describe", "brahma-build-pipeline-job",
        "--region", os.environ["GOOGLE_CLOUD_REGION"],
        "--format=value(spec.template.spec.template.spec.containers[0].image)", stage="Pipeline configured image inspection",
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
