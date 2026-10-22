"""AMD64-DOCKER (ruling SR-T24-AMD64-DOCKER): the runtime probe.  It is run INSIDE the linux/amd64 container, by the same container that then runs the slice, and writes what the
machine there says about itself — `os.uname()`, the Python build, the CPU vendor, the installed-distribution lock — to a file the host reads afterwards.  The architecture of a
qualifying run is READ here, never asserted by the host that started the container (`amd64_docker.runtime_block` refuses a runtime that has no such probe).
Stdlib only; run as `python -I amd64_probe.py --nonce N --out FILE`.  The nonce is chosen by the host per run and echoed back, so a probe file left over from another run is refused.
Output is architecture, versions and hashes only — no chart value."""
import argparse
import hashlib
import json
import os
import platform
import sys
from importlib import metadata

SCHEMA = "ky.amd64_runtime_probe/1"


def cpu_identity() -> dict:
    """First model/vendor lines of /proc/cpuinfo (Rosetta says vendor_id VirtualApple; QEMU says a QEMU model name)."""
    out = {"vendor_id": None, "model_name": None}
    try:
        for line in open("/proc/cpuinfo", encoding="utf-8", errors="replace"):
            k, _, v = line.partition(":")
            k = k.strip()
            if k in out and out[k] is None:
                out[k] = v.strip()
            if all(out.values()):
                break
    except OSError:
        pass
    return out


def dependency_lock_digest() -> tuple[str, int]:
    """sha256 over the sorted `name==version` lines of every installed distribution (the lock the process actually runs on) and their count."""
    lines = sorted({f"{(d.metadata['Name'] or '').lower().replace('_', '-')}=={d.version}" for d in metadata.distributions() if d.metadata["Name"]})
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest(), len(lines)


def swiss_identity() -> dict:
    try:
        import swisseph
        return {"swisseph_module": getattr(swisseph, "__file__", None) and os.path.basename(swisseph.__file__), "swe_version": swisseph.version}
    except Exception as exc:                                              # noqa: BLE001
        return {"error": type(exc).__name__}


def probe(nonce: str) -> dict:
    un = os.uname()
    lock, n = dependency_lock_digest()
    return {"schema": SCHEMA, "source": "in_container", "nonce": nonce, "uname_machine": un.machine, "uname_sysname": un.sysname, "uname_release": un.release,
            "platform_machine": platform.machine(), "sys_platform": sys.platform, "python": platform.python_version(), "python_implementation": platform.python_implementation(),
            "pointer_bits": sys.maxsize.bit_length() + 1, "cpu": cpu_identity(), "dependency_lock_digest": lock, "distributions": n, "swiss": swiss_identity(),
            "dockerenv": os.path.exists("/.dockerenv")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nonce", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    doc = probe(a.nonce)
    tmp = a.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, sort_keys=True)
        f.write("\n")
    os.replace(tmp, a.out)
    print(json.dumps({"uname_machine": doc["uname_machine"], "python": doc["python"], "cpu_vendor": doc["cpu"]["vendor_id"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
