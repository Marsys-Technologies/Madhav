"""The pinned Swiss Ephemeris corpus identity: ONE constant for the Gochara v5 writer and its tests.

The three `.se1` files the kernel opens, with the sha256 the whole project pins. The same digests are enforced at image BUILD time by
`Dockerfile.pipeline` (`sha256sum -c`) and in CI by every `se1` download step; `test_c47_ephe_real_runner.py` asserts that this constant,
those places, `panchang_engine.swiss_backend._PINNED_SHA256` and the gochara conftest all agree, so a re-pin cannot reach one place and
miss another.
"""
from __future__ import annotations

PINNED_SE1_SHA256: dict[str, str] = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}
